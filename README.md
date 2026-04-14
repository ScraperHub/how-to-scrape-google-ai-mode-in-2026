# Google AI Mode sample (Crawlbase + Python)

This folder contains a small CLI that fetches Google Search HTML through the [Crawlbase Crawling API](https://crawlbase.com/crawling-api-avoid-captchas-blocks) and extracts summary candidates, citation-style labels, and outbound links from the returned HTML.

Use it to reproduce the workflow from the companion blog post or to prototype your own selectors.

## Prerequisites

- Python 3.10 or newer
- A [Crawlbase](https://crawlbase.com) account with a **JavaScript** API token (required for most Google SERP / AI-heavy layouts)

## Clone and install

```bash
git clone https://github.com/ScraperHub/how-to-scrape-google-ai-mode-in-2026.git
cd how-to-scrape-google-ai-mode-in-2026/code
```

Then:

```bash
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure API tokens

1. Sign up at [crawlbase.com](https://crawlbase.com) and open your dashboard to copy your tokens.
2. Copy the example env file and add your secrets locally:

   ```bash
   cp .env.example .env
   ```

   On Windows (Command Prompt or PowerShell): `copy .env.example .env`

3. Edit `.env` and set at least **`CRAWLBASE_JS_TOKEN`** for Google. Optionally set **`CRAWLBASE_TOKEN`** if you want to compare the “regular” (non-JS) Crawlbase mode with `--regular-token`.

**Do not commit `.env`** — it is listed in `.gitignore`. Rotate any token that was ever committed or pasted in public chat.

## Run a test

Default: build a standard Google SERP URL from a query, use the JS token, save HTML and JSON:

```bash
python scrape_google_ai_mode.py -q "your search query"
```

This writes:

- `last_response.html` — raw HTML from Crawlbase (useful for tuning parsers when Google changes markup)
- `output.json` — extracted fields (`summary_candidates`, `citations`, `reference_links`)

Skip writing HTML:

```bash
python scrape_google_ai_mode.py -q "your search query" --no-save-html
```

Use a **full Google URL** (for example, an AI Mode or Labs URL copied from your browser):

```bash
python scrape_google_ai_mode.py --url "https://www.google.com/search?q=..."
```

Try the regular Crawlbase token instead of the JS token (often incomplete for heavy JS pages):

```bash
python scrape_google_ai_mode.py -q "your search query" --regular-token
```

Custom output paths:

```bash
python scrape_google_ai_mode.py -q "your search query" --save-html debug.html --json-out results.json
```

## CLI reference

| Option | Description |
|--------|-------------|
| `-q`, `--query` | Search terms; script builds `https://www.google.com/search?...` |
| `--url` | Full Google URL to fetch (overrides `--query`) |
| `--regular-token` | Use `CRAWLBASE_TOKEN` instead of `CRAWLBASE_JS_TOKEN` |
| `--save-html` | Path for raw HTML (default: `last_response.html`) |
| `--json-out` | Path for JSON output (default: `output.json`) |
| `--no-save-html` | Do not write an HTML file |

## Troubleshooting

- **`Missing CRAWLBASE_JS_TOKEN`** — Add `CRAWLBASE_JS_TOKEN` to `.env` or export it in your shell.
- **Empty or odd extractions** — Open `last_response.html`, confirm the page is what you expect (consent interstitial, CAPTCHA text, or a minimal mobile layout). Adjust URL parameters (`hl`, `gl`) or parsing heuristics in `scrape_google_ai_mode.py` as needed.
- **Timeouts** — The script uses a long HTTP timeout for Crawlbase; slow responses can still occur under load.

## Documentation

- [Crawlbase Crawling API](https://crawlbase.com/crawling-api-avoid-captchas-blocks)
- [API documentation](https://crawlbase.com/documentation)

## License

Use and modify this sample in line with your repository’s license and with applicable laws and third-party terms for accessing search results.
