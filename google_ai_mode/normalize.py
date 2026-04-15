"""Normalize Crawlbase Crawling API bodies into a stable blog-oriented schema."""

from __future__ import annotations

import json
from typing import Any


def _parse_body_field(body: Any) -> Any:
    if body is None:
        return None
    if isinstance(body, (dict, list)):
        return body
    if isinstance(body, str):
        s = body.strip()
        if not s:
            return None
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return body
    return body


def _as_link_item(obj: Any) -> dict[str, str] | None:
    if not isinstance(obj, dict):
        return None
    url = obj.get("url") or obj.get("link") or obj.get("href")
    text = (
        obj.get("text")
        or obj.get("title")
        or obj.get("name")
        or obj.get("snippet")
        or ""
    )
    if not url:
        return None
    return {"url": str(url), "text": str(text) if text is not None else ""}


def _collect_link_dicts(node: Any, out: list[dict[str, str]]) -> None:
    if isinstance(node, dict):
        item = _as_link_item(node)
        if item:
            out.append(item)
        for v in node.values():
            _collect_link_dicts(v, out)
    elif isinstance(node, list):
        for el in node:
            _collect_link_dicts(el, out)


def _deep_find_first_str(obj: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and isinstance(obj[k], str) and obj[k].strip():
                return obj[k].strip()
        for v in obj.values():
            found = _deep_find_first_str(v, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for el in obj:
            found = _deep_find_first_str(el, keys)
            if found:
                return found
    return None


def _adapt_crawlbase_google_serp(root: dict[str, Any]) -> dict[str, Any] | None:
    """
    Map Crawlbase ``google-serp`` JSON (``searchResults``, ``peopleAlsoAsk``, …)
    into ``response_text``, ``citations``, and ``links``.

    Google AI Mode pages often still return classic SERP blocks via this scraper;
    we surface snippets as citation text and titles as link labels.
    """
    if "searchResults" not in root:
        return None
    srs = root.get("searchResults") or []
    citations: list[dict[str, str]] = []
    links: list[dict[str, str]] = []
    desc_parts: list[str] = []

    for item in srs:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not url:
            continue
        title = (item.get("title") or "").strip()
        desc = (item.get("description") or "").strip()
        citations.append({"url": str(url), "text": desc or title})
        links.append({"url": str(url), "text": title or desc})
        if desc:
            desc_parts.append(desc)

    for item in root.get("peopleAlsoAsk") or []:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not url:
            continue
        text = (item.get("description") or item.get("title") or "").strip()
        citations.append({"url": str(url), "text": text})
        links.append(
            {
                "url": str(url),
                "text": (item.get("title") or text or "").strip() or text,
            }
        )

    response_text = "\n\n".join(desc_parts[:8]).strip()
    return {
        "response_text": response_text,
        "citations": citations,
        "links": links,
    }


def _deep_find_list_of_linkish(obj: Any, keys: tuple[str, ...]) -> list[dict[str, str]]:
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and isinstance(obj[k], list):
                acc: list[dict[str, str]] = []
                for el in obj[k]:
                    it = _as_link_item(el)
                    if it:
                        acc.append(it)
                if acc:
                    return acc
        for v in obj.values():
            acc = _deep_find_list_of_linkish(v, keys)
            if acc:
                return acc
    elif isinstance(obj, list):
        for el in obj:
            acc = _deep_find_list_of_linkish(el, keys)
            if acc:
                return acc
    return []


def extract_content_fields(parsed_body: Any) -> dict[str, Any]:
    """
    From a parsed ``body`` (dict/list/str), extract ``prompt``, ``response_text``,
    ``citations``, ``links``, and optional ``parse_status_code``.
    """
    root = _parse_body_field(parsed_body)
    serp = _adapt_crawlbase_google_serp(root) if isinstance(root, dict) else None

    prompt = _deep_find_first_str(root, ("prompt", "query", "q", "search_query"))
    response_text = _deep_find_first_str(
        root,
        (
            "response_text",
            "result_text",
            "answer",
            "text",
            "ai_overview",
            "snippet",
        ),
    )
    citations = _deep_find_list_of_linkish(root, ("citations", "sources", "references"))
    links = _deep_find_list_of_linkish(root, ("links", "related_links", "organic_links"))

    if not links and isinstance(root, dict):
        alt: list[dict[str, str]] = []
        for key in ("organic", "results", "searchResults", "peopleAlsoAsk"):
            if key in root:
                _collect_link_dicts(root[key], alt)
        if alt:
            links = alt[:200]

    if serp:
        if serp.get("citations"):
            citations = serp["citations"]
        if serp.get("links"):
            links = serp["links"]
        if not response_text and serp.get("response_text"):
            response_text = serp["response_text"]

    parse_code = None
    if isinstance(root, dict) and "parse_status_code" in root:
        parse_code = root.get("parse_status_code")

    return {
        "prompt": prompt or "",
        "response_text": response_text or "",
        "citations": citations,
        "links": links,
        "parse_status_code": parse_code,
    }


def _preview_body(body: Any, limit: int = 500) -> Any:
    if body is None:
        return None
    if isinstance(body, str):
        return (body[:limit] + "…") if len(body) > limit else body
    try:
        s = json.dumps(body, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(type(body).__name__)
    return (s[:limit] + "…") if len(s) > limit else s


def build_blog_style_result(
    crawl: dict[str, Any],
    *,
    requested_url: str,
    user_prompt: str,
    token_used: str,
    scraper: str | None,
) -> dict[str, Any]:
    """Shape similar to the blog sample: ``results[0].content`` plus metadata."""
    body = crawl.get("body")
    content = extract_content_fields(body)
    if not content.get("prompt"):
        content["prompt"] = user_prompt

    return {
        "results": [
            {
                "content": {
                    "links": content["links"],
                    "prompt": content["prompt"],
                    "citations": content["citations"],
                    "response_text": content["response_text"],
                    "parse_status_code": content.get("parse_status_code"),
                },
                "url": requested_url,
                "status_code": crawl.get("original_status"),
                "pc_status": crawl.get("pc_status"),
                "crawl_url": crawl.get("url"),
                "token_used": token_used,
                "scraper": scraper,
                "raw_body_preview": _preview_body(body),
            }
        ],
    }
