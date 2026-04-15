"""
CLI: scrape Google AI Mode via Crawlbase.

Usage (from ``code/`` directory)::

    pip install -r requirements.txt
    copy .env.example .env
    # edit .env with your Crawlbase regular token
    python -m google_ai_mode "your query here"

Environment (in ``code/.env`` or the process environment):

- ``CRAWLBASE_REGULAR_TOKEN``
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from google_ai_mode.google_ai_mode_scrape import scrape_google_ai_mode


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scrape Google AI Mode (udm=50) via Crawlbase")
    p.add_argument("query", nargs="?", default=os.environ.get("GOOGLE_AI_MODE_QUERY", ""))
    p.add_argument("--gl", default="us")
    p.add_argument("--hl", default="en")
    p.add_argument("--no-scraper", action="store_true", help="Omit scraper=google-serp")
    args = p.parse_args(argv)

    q = (args.query or "").strip()
    if not q:
        p.error("query required (positional or GOOGLE_AI_MODE_QUERY)")

    scraper: str | None = None if args.no_scraper else "google-serp"
    out = scrape_google_ai_mode(q, gl=args.gl, hl=args.hl, scraper=scraper)
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
