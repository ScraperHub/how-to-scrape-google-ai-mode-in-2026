"""
Fetch Google Search / AI-heavy SERP HTML via Crawlbase, then extract summary
candidates, citation-style labels, and outbound reference links.

Google's DOM and URL schemes change often. Treat selectors and default URLs as
starting points: inspect last_response.html and adjust SELECTORS / URL builder.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# URL builder — update when Google changes AI Mode / AI Overview entry URLs.
# Labs "AI Mode" is often reached via Search Labs, not a single stable public
# path. Prefer --url with a value copied from your browser when testing.
# ---------------------------------------------------------------------------

DEFAULT_GOOGLE_HOST = "www.google.com"


def build_google_serp_url(
    query: str,
    *,
    hl: str = "en",
    gl: str = "us",
    host: str = DEFAULT_GOOGLE_HOST,
) -> str:
    """
    Standard web SERP. Many queries still surface AI-generated panels here.
    For Labs AI Mode, pass the full URL with --url instead.
    """
    scheme_netloc = f"https://{host}"
    q = quote(query, safe="")
    # udm=14 disables AI-style layouts — do not use for this project.
    return f"{scheme_netloc}/search?q={q}&hl={hl}&gl={gl}&pws=0"


# ---------------------------------------------------------------------------
# Crawlbase — single integration point (mirrors blog snippets).
# ---------------------------------------------------------------------------

CRAWLBASE_API = "https://api.crawlbase.com/"


def fetch_html_via_crawlbase(target_url: str, *, token: str, timeout: int = 180) -> str:
    """Return raw HTML string from Crawlbase for the fully-qualified target_url."""
    response = requests.get(
        CRAWLBASE_API,
        params={"token": token, "url": target_url},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.text


# ---------------------------------------------------------------------------
# Google href normalization (/url?q=... wrappers).
# ---------------------------------------------------------------------------

GOOGLE_HOST_SUFFIXES = (
    "google.com",
    "googleusercontent.com",
    "gstatic.com",
    "googleapis.com",
)


def _unwrap_google_url(href: str) -> str | None:
    if not href or href.startswith("#"):
        return None
    if href.startswith("/url?"):
        qs = parse_qs(urlparse(href).query)
        if "q" in qs and qs["q"]:
            return unquote(qs["q"][0])
        if "url" in qs and qs["url"]:
            return unquote(qs["url"][0])
        return None
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return None


def resolve_href(href: str) -> str | None:
    """Return a usable absolute URL from a raw <a href> on Google."""
    raw = href.strip()
    unwrapped = _unwrap_google_url(raw)
    if unwrapped:
        return unwrapped
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return None


def _is_external_http(url: str) -> bool:
    try:
        p = urlparse(url)
    except ValueError:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").lower()
    return not any(host == s or host.endswith("." + s) for s in GOOGLE_HOST_SUFFIXES)


# ---------------------------------------------------------------------------
# Selectors / heuristics — tune after inspecting saved HTML.
# ---------------------------------------------------------------------------

SELECTORS = {
    # Primary content column on desktop SERP (when present).
    "main_column": "#center_col, #rcnt",
    # Elements that often carry visible citation labels in AI-style blocks.
    "cite_tags": "cite",
}


def extract_reference_links(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Outbound http(s) links, preferring unwrapped targets."""
    seen: set[str] = set()
    out: list[dict[str, str]] = []

    for a in soup.find_all("a", href=True):
        resolved = resolve_href(a["href"])
        if not resolved:
            continue
        if not _is_external_http(resolved):
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        label = a.get_text(" ", strip=True) or resolved
        out.append({"url": resolved, "anchor_text": label[:500]})

    return out


def extract_citations(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Visible citation strings (domains, titles) from <cite> and nearby text."""
    cites: list[dict[str, str]] = []

    for el in soup.select(SELECTORS["cite_tags"]):
        text = el.get_text(" ", strip=True)
        if text and len(text) > 1:
            cites.append({"kind": "cite", "text": text[:500]})

    # Fallback: link hostnames as lightweight citation proxies.
    for link in extract_reference_links(soup)[:40]:
        host = urlparse(link["url"]).hostname or ""
        if host:
            cites.append({"kind": "host", "text": host})

    # Dedupe by text
    uniq: dict[str, dict[str, str]] = {}
    for c in cites:
        uniq.setdefault(c["text"], c)
    return list(uniq.values())


def extract_summary(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """
    Heuristic summary chunks: long text blocks in the main column with
    moderate link density. Google changes layout frequently; refine after
    inspecting last_response.html.
    """
    main = soup.select_one("#center_col") or soup.select_one("#rcnt") or soup.body
    if not main:
        return []

    candidates: list[tuple[int, str, float]] = []

    for tag in main.find_all(["div", "span", "p", "li"]):
        text = tag.get_text(" ", strip=True)
        if len(text) < 120:
            continue
        links = tag.find_all("a", href=True)
        density = len(links) / max(1, len(text) / 80)
        if density > 0.35:
            continue
        # Skip boilerplate-ish lines
        if re.search(r"^(Images|Videos|News|Maps)\s*$", text[:30], re.I):
            continue
        candidates.append((len(text), text, density))

    candidates.sort(key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    seen_text: set[str] = set()
    for length, text, density in candidates[:12]:
        key = text[:200]
        if key in seen_text:
            continue
        seen_text.add(key)
        results.append(
            {
                "approx_char_len": length,
                "link_density": round(density, 4),
                "text": text[:4000],
            }
        )
    return results


def run(
    *,
    target_url: str,
    token: str,
    save_html_path: str | None,
    json_path: str | None,
) -> dict[str, Any]:
    html = fetch_html_via_crawlbase(target_url, token=token)
    if save_html_path:
        with open(save_html_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(html)

    soup = BeautifulSoup(html, "html.parser")
    payload: dict[str, Any] = {
        "target_url": target_url,
        "summary_candidates": extract_summary(soup),
        "citations": extract_citations(soup),
        "reference_links": extract_reference_links(soup),
    }
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def _resolve_token(use_js: bool) -> str:
    load_dotenv()
    if use_js:
        tok = os.environ.get("CRAWLBASE_JS_TOKEN", "").strip()
        if not tok:
            print("Missing CRAWLBASE_JS_TOKEN in environment or .env", file=sys.stderr)
            sys.exit(1)
        return tok
    tok = os.environ.get("CRAWLBASE_TOKEN", "").strip()
    if not tok:
        print("Missing CRAWLBASE_TOKEN in environment or .env", file=sys.stderr)
        sys.exit(1)
    return tok


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape Google AI-heavy SERP HTML via Crawlbase and extract fields.",
    )
    parser.add_argument("--query", "-q", help="Search query (builds default SERP URL)")
    parser.add_argument(
        "--url",
        help="Full Google URL to fetch (use when targeting Labs AI Mode / copied URL)",
    )
    parser.add_argument(
        "--regular-token",
        action="store_true",
        help="Use CRAWLBASE_TOKEN instead of CRAWLBASE_JS_TOKEN (usually worse for Google AI UI)",
    )
    parser.add_argument(
        "--save-html",
        default="last_response.html",
        help="Write raw HTML from Crawlbase to this path (default: last_response.html)",
    )
    parser.add_argument(
        "--json-out",
        default="output.json",
        help="Write extraction JSON to this path (default: output.json)",
    )
    parser.add_argument(
        "--no-save-html",
        action="store_true",
        help="Do not write raw HTML file",
    )
    args = parser.parse_args()

    if args.url:
        target = args.url
    elif args.query:
        target = build_google_serp_url(args.query)
    else:
        parser.error("Provide --query or --url")

    token = _resolve_token(use_js=not args.regular_token)
    payload = run(
        target_url=target,
        token=token,
        save_html_path=None if args.no_save_html else args.save_html,
        json_path=args.json_out,
    )
    print(json.dumps({k: payload[k] for k in ("target_url",)}, indent=2))
    print(
        json.dumps(
            {
                "summary_chunks": len(payload["summary_candidates"]),
                "citations": len(payload["citations"]),
                "reference_links": len(payload["reference_links"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
