# Thought Process & Design Decisions

# TIME SPENT: 2 hrs

## 1. Understanding the Problem

Before writing any code, I worked through **why** a company like Quartr needs this:

- Quartr makes financial data accessible such as earnings calls, transcripts, reports.
- The 10k is a public disclosure a company provides.
- So quatr might be suing this data for summerising the financial state of a company or create transcript report for stocks


## 2. Key Questions I Explored

### Why PDF specifically?
- SEC filings are served as messy HTML/XBRL — not human-friendly.
- PDF conversion is a **normalisation step** proving I can take unstructured source data and produce clean, portable output.
- The real goal isn't "download a PDF" — it's building a **reliable pipeline** that turns 10k filings into usable data for other teams.

### Does this data change over time?
- New 10-K filings appear once in every FY, but key problem is not all company files it around same months or dates.
- Amended filings can appear at any time of the year which creates uncertainity.
- **Implication:** this is a live, accumulating dataset — not a one-time download and needs monitoring.

### Does Accessing SEC data requires auth or token?
- SEC does not require an API key but has a no more than 10 requests per second from a single source IP
- **Implication:** this can be handled with a 1 sec delay between requests.

### Initial access showed blocker page and the PDF downlaoded showed blockers?
- This happens if rate limits are exceeded or User-Agent is missing.
- **Implication:** code needs to detect this and raise error.

### Why poll daily if filings are annual?
- Companies don't all file on the same day they can vary over a FY or over last few months of a FY not calender year.
- There's no specific date or data telling you when a specific company will file.
- It would also be helpfull for quartr to know when ever these filings happen; the sooner they know the better.
- Daily polling is simple and catches everything within 24 hours; also is simple right as we still unsure of full scope.

### Should we store historical data?
- Storage is cheap as these are PDF. The cost of **not** having history in the future might be **more** due to re-engineering and data loss.
- **Decision:** keep what you fetch, index by accession number so nothing gets overwritten.

### SEC has data in HTML format and we need to convert to PDF. but do we need to keep HTML format?
- Storage is cheap but the question is do we need to keep the HTML format as well. As HTML can be more machine readable it could be helpfull as well for ML/NLP as it can be eaily parsable and cheaper to process.
- Also SEC data is structural data embedded in HTML; which means its not only visual but machine readble; may be in future we dont need NLP to parse it; so HTML can be a future resoucre.
- **Decision:** keep what you fetch, index by accession number so nothing gets overwritten.

### How to deliver to other teams?
- A folder of PDFs is not ideal. The production version should expose data through an **API** and optionally an **event bus**.
- Also more overhead to non-technical people.
- For this assignment scope: webhook notification to teams when a new filing is created.

### What can affect the data quality
- The first and formost is the blocker message showcase while accessing HTML.
- Some files can have encoding or embedding issues( didnt face it but need to be prepared)
- For this assignment scope: We need to by pass even if one company fails.

## 3. Usecase Definition:

Create a reliable, Scalable pipeline to convert the 10-k fillings for different companies to PDF format and make it available to other teams for usage for summerisation, earning calls and stock reports.

## 4. Architecture Decisions

| Decision | Reasoning |
|---|---|
| **Modular package**  | Separate modules for reusability: client, models, pipeline, renderer, manifest, notifier, scheduler |
| **Scalability**  | Make the config in such a way that as if more companies gets added in future it will not be a breaking chnage but just a config change. |
| **Missing Data** | Checking if all the required comaies in the assignment has data fillings downloaded. |
| **JSON based deduplication** | This is the deduplication techniques used where ascension numbe used to keep track of files. With this we also take care of the data validation |
| **Retry with exponential backoff** | SEC rate limits 10 req/sec so we need to handle the retry mechanism to create a time gap|
| **Error handling** | If one companies data fails to be fetched other keeps on; also the code always checks for deduplication |
| **Single browser instance** | Playwright startup is expensive (~2s). Reuse one browser across all PDF renders |
| **Storage** | There are multiple options that we can go through but for now stick with folder loading. This is the simplest solution we can think as we are not sure of full scope. Also this makes it scalable in future even if we want to move to S3 storage or Vector DB |
| **Historical data** | Right now keeping all the historical data that comes in based on data unless a company ammends the 10-k filling; keeping this now as it could be used for model training or pattern identifications |
| **Using Playwright** | SEC fillings fetching is complex as it is in HTML format with nested table, inline css, and asssets. So its good to used a full browser engine to render them. |
| **Temp file for HTML** | Playwright needs a file URI to navigate to (for `<base href>` asset resolution). Use a temp HTML file after converting to PDF this will be deleted(but still scheptical as HTML can be read better for machines.) |
| **Webhook notifier** | Fires a WEBHOOK when a new filing is fetched; teams gets notified |
| **Daily scheduler** | Lightweight `schedule` library. Runs the pipeline once per day. Manifest ensures no duplicate work. For now this is the simplest solution we can keep. |

## 5. Simplification Choices

Throughout the process I actively simplified:

- Removed `argparse` flags (`--force`, `--output-dir`) — unnecessary complexity for the scope.
- Simplified manifest from a nested dict to a simple set of accession numbers. Eralier everything fetched from the fillings were stored in the Manifest files. It made it hard to parse through the Manifest files. So now only saved the numbers to keep track
- Simplified `SecClient` — inlined session setup, removed configurable retry params, kept retry logic but with hardcoded sensible defaults.
- Removed HTML file saving and used them as temp files as PDF was the deliverable
- Seperated the Configs from the pipeline.py to make it reliable.

## 6. What I'd Do Next (Beyond 4 Hours)

- **Tests** — unit tests for the client (mock SEC responses), integration test for the full pipeline.
- **Scheduler** - The entire scheduler can be part of the pipeline or the deployment.
- **Notifier** - setup a teams or slack URL for teams to be notified.
- **Docker** — containerise for consistent deployment for cloud based deployment.
- **CI/CD** - set up the CI/CD and deployment scripts for seamless deployments.
- **Manifest** — This approach might not be right as it can create a longer manifest in the longer run and if overriding chances at the time of amendments. Might need a proper version controlling.
- **Database** — replace JSON manifest with Postgres for queryable filing metadata or vector DB as well like opensource options Qdrant.This can help with non-technical teams as well
- **REST API** — `GET /filings?ticker=AAPL&form=10-K&latest=true` so other teams consume data without looking into storage and also helps with extraction.
- **Section Summary** — Can non-technical teams to understand what changed in the files.
- **Data lineage** - The manifest can be used to figure out when the data was fetched with the accension numbers and figure out data lineage.
- **Schema Evalution** - What if SEC Changes the schema or data format for fetching the files ( API response and path chnages); this needs to be proporly tracked and notified to avoid breakages in code runs.
- **Data History** - Historical data is always valuable form a ML or DE perspective; what if we need to store 10 yrs of data for evaluation we might need advanced stoarge options which are low cost as well.


## 7. AI Tool Usage

The AI was used as a collaborative tool. I drove the design decisions, questioned assumptions, and iteratively simplified the implementation. Used AI for coding help.
