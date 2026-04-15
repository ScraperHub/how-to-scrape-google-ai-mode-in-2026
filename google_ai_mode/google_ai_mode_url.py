"""Build Google Search URLs for AI Mode (udm=50)."""

from __future__ import annotations

from urllib.parse import quote_plus, urlencode


def build_google_ai_mode_search_url(
    query: str,
    *,
    gl: str = "us",
    hl: str = "en",
    uule: str | None = None,
) -> str:
    """
    Return a https://www.google.com/search URL that opens AI Mode.

    ``uule`` is optional encoded location (see Google's uule parameter).
    """
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    params: list[tuple[str, str]] = [
        ("udm", "50"),
        ("q", query.strip()),
        ("gl", gl),
        ("hl", hl),
    ]
    if uule:
        params.append(("uule", uule))
    qs = urlencode(params, quote_via=quote_plus, safe="")
    return f"https://www.google.com/search?{qs}"
