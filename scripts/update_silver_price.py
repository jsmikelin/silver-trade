"""Build the public silver chart feed from the authorized GoldAPI history API."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path

from decouple import config

GOLD_API_HISTORY_URL = "https://api.gold-api.com/history"
GOLD_API_SOURCE_URL = "https://gold-api.com/docs"
ALLOWED_SOURCE_HOST = "api.gold-api.com"
DEFAULT_HISTORY_DAYS = 30


def get_api_key() -> str:
    """Read the key from the process environment or the local ignored .env file."""
    return str(config("GOLD_API_KEY", default="")).strip()


def fetch_gold_api_history(
    api_key: str,
    *,
    history_days: int = DEFAULT_HISTORY_DAYS,
    fetched_at: datetime | None = None,
    max_attempts: int = 3,
) -> list[dict]:
    if not api_key:
        raise ValueError("GOLD_API_KEY is required")
    if history_days < 2:
        raise ValueError("history_days must be at least 2")

    fetched_at = fetched_at or datetime.now(timezone.utc)
    fetched_at = fetched_at.astimezone(timezone.utc)
    # Exclude the current UTC day so the chart never contains a partial daily average.
    end_at = datetime.combine(fetched_at.date(), datetime_time.min, timezone.utc)
    start_at = end_at - timedelta(days=max(history_days * 2, 45))
    query = urllib.parse.urlencode(
        {
            "symbol": "XAG",
            "startTimestamp": int(start_at.timestamp()),
            "endTimestamp": int((end_at - timedelta(seconds=1)).timestamp()),
            "groupBy": "day",
            "aggregation": "avg",
            "orderBy": "asc",
        }
    )
    url = f"{GOLD_API_HISTORY_URL}?{query}"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_SOURCE_HOST:
        raise ValueError("GoldAPI source URL must use the approved HTTPS host")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "HelinSilverPriceUpdater/2.0 (+https://helinsilver.com)",
                "x-api-key": api_key,
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError(f"GoldAPI returned HTTP {response.status}")
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, list):
                raise ValueError("GoldAPI history response must be a list")
            return payload
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))
    raise RuntimeError(f"GoldAPI fetch failed after {max_attempts} attempts") from last_error


def build_price_payload(
    records: list[dict],
    *,
    history_days: int = DEFAULT_HISTORY_DAYS,
    fetched_at: datetime | None = None,
) -> dict:
    if history_days < 2:
        raise ValueError("history_days must be at least 2")
    fetched_at = fetched_at or datetime.now(timezone.utc)
    today = fetched_at.astimezone(timezone.utc).date()
    daily_prices: dict[date, float] = {}

    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            market_date = datetime.fromisoformat(str(record.get("day", ""))).date()
            usd_per_ounce = float(record["avg_price"])
        except (KeyError, TypeError, ValueError):
            continue
        if (
            market_date >= today
            or market_date.weekday() >= 5
            or not 0.1 <= usd_per_ounce <= 500
        ):
            continue
        daily_prices[market_date] = round(usd_per_ounce, 3)

    ordered = sorted(daily_prices.items())
    if len(ordered) < 2:
        raise ValueError("GoldAPI response did not contain enough valid daily USD prices")
    history = ordered[-history_days:]
    previous_price = history[-2][1]
    latest_date, latest_price = history[-1]
    change = round(latest_price - previous_price, 3)
    change_pct = round((change / previous_price) * 100, 3)

    return {
        "schema_version": 2,
        "benchmark": "GoldAPI Silver Daily Average",
        "price_type": "daily_average",
        "price": latest_price,
        "change": change,
        "change_pct": change_pct,
        "market_date": latest_date.isoformat(),
        "fetched_at": fetched_at.astimezone(timezone.utc).isoformat(),
        "currency": "USD",
        "unit": "troy_ounce",
        "source": {
            "name": "GoldAPI",
            "url": GOLD_API_SOURCE_URL,
            "data_url": GOLD_API_HISTORY_URL,
        },
        "history": [
            {"date": market_date.isoformat(), "price": price}
            for market_date, price in history
        ],
    }


def write_json_atomic(output_path: Path, payload: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output_path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def update_price_file(
    output_path: Path,
    *,
    api_key: str,
    history_days: int = DEFAULT_HISTORY_DAYS,
) -> dict:
    fetched_at = datetime.now(timezone.utc)
    records = fetch_gold_api_history(
        api_key,
        history_days=history_days,
        fetched_at=fetched_at,
    )
    payload = build_price_payload(
        records,
        history_days=history_days,
        fetched_at=fetched_at,
    )
    try:
        existing = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        existing = None
    if isinstance(existing, dict):
        existing_comparable = {
            key: value for key, value in existing.items() if key != "fetched_at"
        }
        payload_comparable = {
            key: value for key, value in payload.items() if key != "fetched_at"
        }
        if existing_comparable == payload_comparable:
            return existing
    write_json_atomic(output_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("api/live-price.json"))
    parser.add_argument("--history-days", type=int, default=DEFAULT_HISTORY_DAYS)
    args = parser.parse_args()
    payload = update_price_file(
        args.output,
        api_key=get_api_key(),
        history_days=args.history_days,
    )
    print(
        f"Updated {args.output} with {payload['benchmark']} "
        f"for {payload['market_date']}: ${payload['price']:.3f}/oz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
