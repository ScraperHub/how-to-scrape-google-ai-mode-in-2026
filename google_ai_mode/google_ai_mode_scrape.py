"""

Orchestrate Crawlbase requests for Google AI Mode (``udm=50``) using the regular Crawlbase token.



Crawlbase ``google-serp`` often returns classic SERP JSON (``searchResults``, …) even for

AI Mode URLs; :mod:`google_ai_mode.normalize` maps those fields into ``response_text``,

``citations``, and ``links``. Native AI narrative JSON, when present, takes precedence.

"""



from __future__ import annotations



import os

from pathlib import Path

from typing import Any



try:

    from dotenv import load_dotenv



    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

except ImportError:

    pass



from google_ai_mode.crawlbase_client import fetch_crawlbase_json

from google_ai_mode.google_ai_mode_url import build_google_ai_mode_search_url

from google_ai_mode.normalize import build_blog_style_result





def _load_regular_token() -> str | None:

    return os.environ.get("CRAWLBASE_REGULAR_TOKEN")





def scrape_google_ai_mode(

    query: str,

    *,

    gl: str = "us",

    hl: str = "en",

    uule: str | None = None,

    scraper: str | None = "google-serp",

    timeout: float = 90.0,

) -> dict[str, Any]:

    """

    Fetch Google AI Mode for ``query`` via Crawlbase Crawling API (regular token only).

    """

    token = _load_regular_token()

    if not token:

        raise ValueError(

            "Set CRAWLBASE_REGULAR_TOKEN in code/.env or the environment; see .env.example"

        )



    target_url = build_google_ai_mode_search_url(query, gl=gl, hl=hl, uule=uule)

    last = fetch_crawlbase_json(target_url, token=token, scraper=scraper, timeout=timeout)

    return build_blog_style_result(

        last,

        requested_url=target_url,

        user_prompt=query.strip(),

        token_used="regular",

        scraper=scraper,

    )

