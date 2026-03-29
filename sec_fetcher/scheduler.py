"""Daily scheduler — runs the SEC fetcher once per day.

Usage:
    python -m sec_fetcher.scheduler          # runs daily at 08:00 by default
    python -m sec_fetcher.scheduler --time 14:30  # runs daily at 14:30
"""

from __future__ import annotations

import argparse
import logging
import time

import schedule

from sec_fetcher.cli import main as run_pipeline
from sec_fetcher.config import WEBHOOK_URL
from sec_fetcher.notifier import notify_run_failure

log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Schedule the SEC 10-K fetcher to run daily",
    )
    parser.add_argument(
        "--time",
        default="08:00",
        help="Time to run daily in HH:MM format (default: 08:00)",
    )
    return parser.parse_args()


def scheduler() -> None:
    log.info("Starting scheduled SEC 10-K fetch")
    try:
        run_pipeline()
        log.info("Scheduled run completed successfully")
    except SystemExit:
        pass
    except Exception as exc:
        log.error("Scheduled run failed: %s", exc)
        notify_run_failure(WEBHOOK_URL, str(exc))


def main() -> None:

    args = parse_args()

    schedule.every().day.at(args.time).do(scheduler)
    log.info("Scheduled to run daily at %s", args.time)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
