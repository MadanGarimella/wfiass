
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION = httpx.Client(
    headers={"Accept": "application/json"},
    timeout=60.0,
)


def extract_records(payload):
    """Normalize common API response formats into a list of records."""
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "results", "result"):
            if isinstance(payload.get(key), list):
                return payload[key]

        raise ValueError(
            "Unexpected API response structure. "
            f"Received object keys: {list(payload.keys())}"
        )

    raise ValueError(
        f"Unexpected API response type: {type(payload).__name__}"
    )


def fetch_json(endpoint, params):
    """Request data from Elexon's API with diagnostic error messages."""
    url = f"{BASE_URL}{endpoint}"

    try:
        response = SESSION.get(url, params=params)
        response.raise_for_status()
        return extract_records(response.json())

    except httpx.HTTPStatusError as exc:
        print(f"API HTTP error: {exc.response.status_code}")
        print(f"Request URL: {exc.request.url}")
        print(f"Response: {exc.response.text[:1000]}")
        raise

    except httpx.RequestError as exc:
        print(f"Network error while requesting {url}: {exc}")
        raise

    except ValueError as exc:
        print(f"Could not interpret API response: {exc}")
        raise


def save_json(filename, records):
    """Save retrieved records as formatted JSON."""
    path = DATA_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2, default=str)

    print(f"Saved {len(records):,} records to {path}")


def fetch_actual_wind():
    """Fetch actual wind generation for January 2026."""
    print("\nFetching actual wind generation...")

    records = fetch_json(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": "2026-01-01",
            "settlementDateTo": "2026-01-31",
            "fuelType": "WIND",
        },
    )

    if records:
        df = pd.DataFrame(records)

        if "fuelType" in df.columns:
            df = df[
                df["fuelType"].astype(str).str.upper() == "WIND"
            ]

        if "startTime" in df.columns:
            timestamps = pd.to_datetime(
                df["startTime"], utc=True, errors="coerce"
            )

            df = df[
                (timestamps >= "2026-01-01T00:00:00Z")
                & (timestamps < "2026-02-01T00:00:00Z")
            ]

        records = df.to_dict(orient="records")

    save_json("actual_wind_january_2026.json", records)


def fetch_wind_forecasts():
    """
    Fetch forecast publications from December 2025 through January 2026.

    Filter delivery timestamps to January while preserving publishTime.
    """
    print("\nFetching wind forecasts...")

    start = datetime(2025, 12, 1, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)

    all_records = []
    current = start

    while current < end:
        window_end = min(current + timedelta(days=7), end)

        params = {
            "publishDateTimeFrom": current.isoformat(),
            "publishDateTimeTo": window_end.isoformat(),
        }

        print(
            f"Publication window: {current.isoformat()} "
            f"to {window_end.isoformat()}"
        )

        records = fetch_json("/datasets/WINDFOR/stream", params)

        print(f"Retrieved {len(records):,} records")
        all_records.extend(records)

        current = window_end
        time.sleep(0.25)

    df = pd.DataFrame(all_records)

    if not df.empty:
        dedup_columns = [
            col
            for col in ("publishTime", "startTime", "generation")
            if col in df.columns
        ]

        if dedup_columns:
            df = df.drop_duplicates(subset=dedup_columns)

        if "startTime" in df.columns:
            timestamps = pd.to_datetime(
                df["startTime"], utc=True, errors="coerce"
            )

            df = df[
                (timestamps >= "2026-01-01T00:00:00Z")
                & (timestamps < "2026-02-01T00:00:00Z")
            ]

        all_records = df.to_dict(orient="records")

    save_json("wind_forecasts_january_2026.json", all_records)


if __name__ == "__main__":
    try:
        print("Elexon wind data retrieval")
        print("=" * 35)

        fetch_actual_wind()
        fetch_wind_forecasts()

        print("\nData retrieval completed.")

    finally:
        SESSION.close()
