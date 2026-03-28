# SEC 10-K Report Fetcher

Creates a reliable, Scalable pipeline that **Extract, Transform** and **Load** latest 10-K annual reports from the SEC EDGAR API for a set of
companies and converts them to PDF.

**Companies:** Apple, Meta, Alphabet, Amazon, Netflix, Goldman Sachs

## Time Spend:

| Category | Time (hrs) |
|----------|---------|
| [THOUGHT_PROCESS.md](THOUGHT_PROCESS.md) | 2 |
| Coding and debugging | 2 |

## Approach

> **Start here → [THOUGHT_PROCESS.md](THOUGHT_PROCESS.md)**
> Covers: problem understanding, SEC API research, architecture decisions, simplification, and what I'd build next.

### Mindmap

> ![Design Mindmap](assets/Quartr_Solution_Design.png)
> [View the design mindmap on Figma](https://www.figma.com/board/0Vr7GPBXFs2gTlZZIlWQkw/Quartr_Solution_Design?node-id=21-3132&t=hEatoDgM1JnYYkYe-0)

Quartr makes financial data accessible. The 10-K is the most comprehensive public
disclosure a company produces such as revenue breakdowns, risk factors..etc. This
service turns raw SEC filings into a reliable pipeline that feeds downstream products.

## Project Structure

```
sec_fetcher/
├── __init__.py       # Package marker
├── __main__.py       # Entry point (python -m sec_fetcher)
├── cli.py            # CLI orchestration; integrates everything together
├── client.py         # SEC EDGAR API client
├── config.py         # Config files including company info and USER_AGENT
├── manifest.py       # Accession-number tracking
├── models.py         # Filing and FilingResult dataclasses(2 dataclasses)
├── notifier.py       # Webhook notifications
├── pipeline.py       # fetch(EXTRACT) → transform → record(LOAD)
├── renderer.py       # HTML to PDF with Playwright
└── scheduler.py      # Daily scheduling with the scheduler lib.
```

### Reliability & Scalability

- **Retries with exponential backoff** 4xx/5xx responses: SEC has rate limits (10 req/sec) handles with in code with sleep.
- **Error handling** — checks if all required company info is downloaded and also check when one company info is failed to fetch others will be continued
- **Manifest-based deduplication(JSON)** — a `manifest.json` tracks fetched filings by accession number. Since the file is schedules it skips if there is no change in filling. Incase of ammendment it is overwritten but in case of new filling a new version created.
- **Single browser instance** reused across all PDF rendering to avoid repeated startup overhead.
- **Webhook notifications** — optionally POST to a Slack/Teams webhook when a new filing is fetched. This can help with the teams to know when a new filing comes and monitoring if the fetching fails.
- **Daily scheduler** — run continuously with `python -m sec_fetcher.scheduler` and it will fetch once per day.

## Prerequisites

- Python 3.10+

## Setup & Run

```bash
# Create and activate a virtual environment
python3 -m venv quartr
source quartr/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install the Playwright Chromium browser (required once)
playwright install chromium

# Run the fetcher
python -m sec_fetcher
```

### Scheduler

Run the fetcher automatically once per day:

```bash
python -m sec_fetcher.scheduler              # daily at 08:00 (default)
python -m sec_fetcher.scheduler --time 14:30  # daily at 14:30
```

## Configuration

Edit `sec_fetcher/config.py`:

| Constant | Purpose |
|----------|---------|
| `USER_AGENT` | SEC requires a USER_AGENT in the fomat real name + email; else the API fails |
| `COMPANIES` | This is the company names that we need information from SEC; Can add or remove based on what we need |
| `REQUEST_DELAY_SECONDS` |As SEC has rate liniting; Delay between SEC requests (default 1 s). |
| `WEBHOOK_URL` | Optional webhook URL for new-filing notifications as this can be a slack or teams webhook URL(default is None). |

## How It Works

1. GETs each company's CIK number from SEC ticker via the SEC company tickers endpoint.
2. create a ticker map from the optained ticker list.
2. GET request to the EDGAR submissions API to find the most recent 10-K filing based on the mapping.
3. Downloads the filing HTML from the SEC Archives.
4. Renders the HTML to PDF using Playwright.
5. Records the accession number in a manifest to avoid duplication and stores the HTML as well.
6. Set a scheduler to run it everyday.
7. Set up a notifier for letting the teams know when ever there is a new filling.

Output PDFs are saved to the `sec_10k_pdfs/` directory.

## SEC API References

- Company tickers: https://www.sec.gov/files/company_tickers.json
- Submissions: https://data.sec.gov/submissions/CIK{cik}.json
- How to use SEC API: https://blog.greenflux.us/so-you-want-to-integrate-with-the-sec-api/
- Info on 10k fillings : https://www.dfinsolutions.com/knowledge-hub/thought-leadership/knowledge-resources/what-10-k-filing

## Solution Design

See [THOUGHT_PROCESS.md](THOUGHT_PROCESS.md) for the detailed solution design.


See the design discussion below for how this fits into a production data platform.

### Output

**First run — fetches all 6 filings:**
![First run output](assets/first_run.png)


**Second run — manifest skips all 6 (deduplication):**
![Pipeline output with manifest deduplication](assets/outcome_with_skipping.png)

## Production Architecture (Beyond This Script)

| Layer | What | Why |
|---|---|---|
| **Scheduled ingestion** | Daily cron polling SEC | Companies file on unpredictable dates across a ~5-month window in a FY |
| **Object storage** | S3 storage  | Durable, versioned, cheap ( if we need to store 10yrs of data)|
| **Metadata DB** | Postgres table of filing metadata | Queryable catalog |
| **REST API** | `GET /filings?ticker=AAPL&form=10-K` ( example)| Downstream teams consume filings without touching storage |
| **Event bus** | `filing.ingested`,`filing.missed`, `filing.ammended` events ( example) | NLP pipelines and alerts react in real time |
| **Data lineage** | The manifest can be used to figure out when the data was fetched with the accension numbers and figure out data lineage |
| **Observability** | Observability beyond just logs add Grafana or Prometheous for advanced observability and metrics storage. |

