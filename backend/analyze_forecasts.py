import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

DECISION_CUTOFF_HOUR_UTC = 23
DECISION_CUTOFF_MINUTE_UTC = 0


def load_json(filename):
    path = DATA_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        return pd.DataFrame(json.load(file))


def load_actuals():
    """Convert half-hourly actual generation to hourly averages."""
    df = load_json("actual_wind_january_2026.json")

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["generation"] = pd.to_numeric(
        df["generation"], errors="coerce"
    )

    df = df.dropna(subset=["startTime", "generation"])

    df["deliveryHour"] = df["startTime"].dt.floor("h")

    hourly = (
        df.groupby("deliveryHour", as_index=False)
        .agg(actualGeneration=("generation", "mean"))
    )

    return hourly


def load_forecasts():
    """Load forecast publications and preserve their publication times."""
    df = load_json("wind_forecasts_january_2026.json")

    df["publishTime"] = pd.to_datetime(
        df["publishTime"], utc=True, errors="coerce"
    )
    df["startTime"] = pd.to_datetime(
        df["startTime"], utc=True, errors="coerce"
    )
    df["generation"] = pd.to_numeric(
        df["generation"], errors="coerce"
    )

    df = df.dropna(
        subset=["publishTime", "startTime", "generation"]
    )

    df = df.rename(
        columns={
            "startTime": "deliveryHour",
            "generation": "forecastGeneration",
        }
    )

    return df


def select_latest_forecasts(forecasts):
    """
    Select the latest forecast published at or before the
    provisional decision cutoff for each delivery hour.

    The cutoff is evaluated separately for each delivery date.
    All timestamps are timezone-aware UTC timestamps.
    """
    df = forecasts.copy()

    df["decisionCutoff"] = (
        df["deliveryHour"].dt.normalize()
        - pd.Timedelta(days=1)
        + pd.Timedelta(
            hours=DECISION_CUTOFF_HOUR_UTC,
            minutes=DECISION_CUTOFF_MINUTE_UTC,
        )
    )

    # Exclude forecasts published after the decision cutoff.
    eligible = df.loc[
        df["publishTime"] <= df["decisionCutoff"]
    ].copy()

    if eligible.empty:
        return eligible

    # Select the latest eligible publication for each delivery hour.
    eligible = eligible.sort_values(
        ["deliveryHour", "publishTime"]
    )

    selected = eligible.drop_duplicates(
        subset=["deliveryHour"],
        keep="last",
    )

    return selected


def calculate_metrics(df):
    """Calculate forecast accuracy on matched observations."""
    if df.empty:
        return None

    errors = df["forecastGeneration"] - df["actualGeneration"]

    return {
        "matched_hours": int(len(df)),
        "coverage_percent": round(len(df) / 744 * 100, 2),
        "mae": round(errors.abs().mean(), 2),
        "rmse": round((errors.pow(2).mean()) ** 0.5, 2),
        "bias": round(errors.mean(), 2),
    }


def main():
    print("Loading actual generation and forecasts...")

    actuals = load_actuals()
    forecasts = load_forecasts()

    print(f"Hourly actual observations: {len(actuals):,}")
    print(f"Forecast records: {len(forecasts):,}")

    selected = select_latest_forecasts(forecasts)

    print(f"Delivery hours with eligible forecasts: {len(selected):,}")

    matched = selected.merge(
        actuals,
        on="deliveryHour",
        how="inner",
        validate="one_to_one",
    )

    matched["forecastError"] = (
        matched["forecastGeneration"] - matched["actualGeneration"]
    )

    print(f"Matched delivery hours: {len(matched):,}")

    metrics = calculate_metrics(matched)

    if metrics is None:
        print(
            "\nNo matched observations. Check the decision cutoff "
            "and forecast publication coverage."
        )
        return

    print("\nForecast accuracy metrics:")
    for name, value in metrics.items():
        print(f"{name}: {value}")

    matched_path = DATA_DIR / "forecast_analysis_january_2026.csv"
    matched.to_csv(matched_path, index=False)

    print(f"\nSaved matched analysis to: {matched_path}")


if __name__ == "__main__":
    main()
