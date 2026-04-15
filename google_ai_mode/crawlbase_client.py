"""Minimal Crawlbase Crawling API client."""

from __future__ import annotations

from typing import Any

import requests

CRAWLBASE_API = "https://api.crawlbase.com/"


def fetch_crawlbase_json(
    target_url: str,
    *,
    token: str,
    scraper: str | None = None,
    response_format: str = "json",
    timeout: float = 90.0,
    extra_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    GET Crawling API with ``format=json``.

    Returns the parsed top-level JSON (``original_status``, ``pc_status``, ``url``, ``body``, ...).
    """
    params: dict[str, Any] = {
        "token": token,
        "url": target_url,
        "format": response_format,
    }
    if scraper is not None and scraper != "":
        params["scraper"] = scraper
    if extra_params:
        for k, v in extra_params.items():
            if v is None:
                continue
            params[k] = "true" if v is True else ("false" if v is False else v)

    headers = {"Accept-Encoding": "gzip, deflate"}
    resp = requests.get(CRAWLBASE_API, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
