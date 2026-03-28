FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium

COPY sec_fetcher/ sec_fetcher/

# Output directory; if not will be created in code.
RUN mkdir -p sec_10k_pdfs

# Default: run the fetcher once (sec_fetcher.scheduler will handle scheduling at default time)
CMD ["python", "-m", "sec_fetcher"]
