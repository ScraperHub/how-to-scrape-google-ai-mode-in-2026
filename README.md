# Google AI Mode (udm=50) — Python sample

Small Python package that calls the [Crawlbase Crawling API](https://crawlbase.com/) for a Google Search URL in **AI Mode** (`udm=50`), then normalizes the Crawlbase JSON into a stable shape: prompt, `response_text`, `citations`, and `links`.

Repository: [github.com/ScraperHub/how-to-scrape-google-ai-mode-in-2026](https://github.com/ScraperHub/how-to-scrape-google-ai-mode-in-2026)

## What you need

- **Python 3.10+**
- A [Crawlbase](https://crawlbase.com/) account and a **regular** Crawling API token (set as `CRAWLBASE_REGULAR_TOKEN` in `.env`)

## Clone and install

```bash
git clone https://github.com/ScraperHub/how-to-scrape-google-ai-mode-in-2026.git
cd how-to-scrape-google-ai-mode-in-2026
```

Use the directory that contains **`requirements.txt`** and the **`google_ai_mode`** package (in this layout that is the `code` folder):

```bash
cd code
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **macOS / Linux:** `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configure the token

1. In the Crawlbase dashboard, copy your **normal / regular** token for the Crawling API.
2. Copy the example env file and edit `.env` (same folder as `requirements.txt`):

   ```bash
   cp .env.example .env
   ```

   On Windows (Command Prompt or PowerShell):

   ```text
   copy .env.example .env
   ```

3. Set **`CRAWLBASE_REGULAR_TOKEN`** to that value.

Do **not** commit `.env`; it is listed in `.gitignore`. Rotate any token that was committed or pasted in public chat.

## Run the CLI

From the directory that contains `requirements.txt` (and with the venv activated):

```bash
python -m google_ai_mode "your search query"
```

JSON is printed to **stdout** (pretty-printed). Redirect if you want a file:

```bash
python -m google_ai_mode "your search query" > output.json
```

You can pass the query via **`GOOGLE_AI_MODE_QUERY`** in `.env` instead of a positional argument, then run:

```bash
python -m google_ai_mode
```

### CLI options

| Option | Description |
|--------|-------------|
| `query` | Positional search string (optional if `GOOGLE_AI_MODE_QUERY` is set). |
| `--gl` | Google `gl` parameter (default: `us`). |
| `--hl` | Google `hl` parameter (default: `en`). |
| `--no-scraper` | Omit Crawlbase `scraper=google-serp` (default is to send it). |

## Output shape

The top-level object has a `results` array with one item. Useful fields include:

- **`results[0].content`**: `prompt`, `response_text`, `citations`, `links`, `parse_status_code`
- **`results[0].url`**: Google AI Mode URL that was requested
- **`results[0].status_code`**, **`pc_status`**, **`crawl_url`**, **`token_used`**, **`scraper`**
- **`results[0].raw_body_preview`**: Short preview of the raw `body` from Crawlbase (for debugging parsers)

## Use as a library

With `PYTHONPATH` or from an environment where the package is installed:

```python
from google_ai_mode import scrape_google_ai_mode

data = scrape_google_ai_mode("example query", gl="us", hl="en")
```

## Troubleshooting

- **`Set CRAWLBASE_REGULAR_TOKEN…`** — Add the variable to `.env` or export it in your shell, then rerun from the same directory so `python-dotenv` can load `code/.env` (when the package lives under `code/`).
- **`401` / Crawlbase errors** — Confirm the token type matches a regular Crawling API token and that billing or limits are not blocking requests.
- **Sparse `response_text` / odd `citations`** — Inspect `raw_body_preview` and Crawlbase’s `body`; Google and Crawlbase payloads change over time. Adjust parsing in `google_ai_mode/normalize.py` if needed.

## Documentation

- [Crawlbase Crawling API](https://crawlbase.com/)

## License

Use and modify this sample in line with your repository’s license and with applicable laws and third-party terms for accessing search results.
