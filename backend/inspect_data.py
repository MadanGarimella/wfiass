import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def load_json(filename):
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    return pd.DataFrame(records)


def inspect_actuals():
    print("\n" + "=" * 60)
    print("ACTUAL WIND GENERATION")
    print("=" * 60)

    df = load_json("actual_wind_january_2026.json")

    if df.empty:
        print("ERROR: No actual generation records found.")
        return

    print(f"Total records: {len(df):,}")

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)

    print(f"First delivery: {df['startTime'].min()}")
    print(f"Last delivery:  {df['startTime'].max()}")
    print(f"Unique delivery timestamps: {df['startTime'].nunique():,}")
    print(f"Duplicate delivery timestamps: {df['startTime'].duplicated().sum():,}")
    print(f"Missing generation values: {df['generation'].isna().sum():,}")

    daily = df.groupby(df["startTime"].dt.date).size()

    print(f"Days represented: {len(daily)}")
    print("Records per day:")
    print(daily.to_string())


def inspect_forecasts():
    print("\n" + "=" * 60)
    print("WIND FORECASTS")
    print("=" * 60)

    df = load_json("wind_forecasts_january_2026.json")

    if df.empty:
        print("ERROR: No forecast records found.")
        return

    print(f"Total records: {len(df):,}")

    df["publishTime"] = pd.to_datetime(
        df["publishTime"], utc=True, errors="coerce"
    )
    df["startTime"] = pd.to_datetime(
        df["startTime"], utc=True, errors="coerce"
    )

    print(f"First publication: {df['publishTime'].min()}")
    print(f"Last publication:  {df['publishTime'].max()}")
    print(f"Unique publication timestamps: {df['publishTime'].nunique():,}")

    print(f"First delivery: {df['startTime'].min()}")
    print(f"Last delivery:  {df['startTime'].max()}")
    print(f"Unique delivery timestamps: {df['startTime'].nunique():,}")

    print(f"Missing publication timestamps: {df['publishTime'].isna().sum():,}")
    print(f"Missing delivery timestamps: {df['startTime'].isna().sum():,}")
    print(f"Missing generation values: {df['generation'].isna().sum():,}")

    duplicate_columns = [
        column
        for column in ["publishTime", "startTime", "generation"]
        if column in df.columns
    ]

    print(
        "Duplicate publication-delivery-value rows:",
        f"{df.duplicated(subset=duplicate_columns).sum():,}",
    )

    print("\nRecords per publication date:")
    publication_counts = (
        df.groupby(df["publishTime"].dt.date)
        .size()
        .sort_index()
    )
    print(publication_counts.to_string())

    print("\nSample forecast records:")
    print(
        df[["publishTime", "startTime", "generation"]]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    inspect_actuals()
    inspect_forecasts()
