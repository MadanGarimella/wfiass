from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

ANALYSIS_FILE = (
    BASE_DIR / "data" / "forecast_analysis_january_2026.csv"
)

# This is the provisional cutoff used by the current
# analysis script. Confirm it against the business
# decision process before treating results as final.
DECISION_CUTOFF = "23:00 UTC on the previous calendar day"

app = FastAPI(
    title="Wind Forecast Intelligence API",
    description=(
        "API for analyzing UK wind generation forecasts "
        "and actual generation for January 2026."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Data loading
# --------------------------------------------------

def load_analysis() -> pd.DataFrame:
    """Load and validate the precomputed analysis dataset."""

    if not ANALYSIS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis CSV not found. "
                "Run analyze_forecasts.py first."
            ),
        )

    try:
        df = pd.read_csv(ANALYSIS_FILE)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read analysis CSV: {exc}",
        )

    required_columns = {
        "deliveryHour",
        "publishTime",
        "forecastGeneration",
        "actualGeneration",
        "forecastError",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis CSV is missing required columns: "
                f"{sorted(missing_columns)}"
            ),
        )

    df = df.copy()

    for column in ["deliveryHour", "publishTime"]:
        df[column] = pd.to_datetime(
            df[column],
            utc=True,
            errors="coerce",
        )

    numeric_columns = [
        "forecastGeneration",
        "actualGeneration",
        "forecastError",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "deliveryHour",
            "publishTime",
            "forecastGeneration",
            "actualGeneration",
            "forecastError",
        ]
    )

    if df.empty:
        raise HTTPException(
            status_code=500,
            detail="The analysis dataset contains no valid observations.",
        )

    if df["deliveryHour"].duplicated().any():
        raise HTTPException(
            status_code=500,
            detail=(
                "The analysis CSV contains duplicate delivery hours. "
                "Each delivery hour must have one selected forecast."
            ),
        )

    return df.sort_values("deliveryHour").reset_index(drop=True)


def calculate_metrics(df: pd.DataFrame) -> dict:
    """Calculate forecast accuracy metrics from matched observations."""

    if df.empty:
        return {
            "matched_hours": 0,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
        }

    errors = (
        df["forecastGeneration"] - df["actualGeneration"]
    ).to_numpy(dtype=float)

    return {
        "matched_hours": int(len(df)),
        "mae_mw": round(float(np.mean(np.abs(errors))), 2),
        "rmse_mw": round(float(np.sqrt(np.mean(errors ** 2))), 2),
        "bias_mw": round(float(np.mean(errors)), 2),
    }


def serialize_records(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame into JSON-friendly records."""

    result = df.copy()

    for column in ["deliveryHour", "publishTime"]:
        if column in result.columns:
            result[column] = (
                result[column]
                .dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            )

    return result.replace(
        {np.nan: None}
    ).to_dict(orient="records")


# --------------------------------------------------
# API endpoints
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    """Check whether the API and analysis file are available."""

    return {
        "status": "ok",
        "service": "Wind Forecast Intelligence API",
        "analysis_file_exists": ANALYSIS_FILE.exists(),
    }


@app.get("/api/metadata")
def get_metadata():
    """Describe the dataset and the current analysis assumptions."""

    df = load_analysis()

    return {
        "product": "Wind Forecast Intelligence",
        "geography": "United Kingdom national-level wind generation",
        "actual_dataset": "FUELHH",
        "forecast_dataset": "WINDFOR",
        "period": "January 2026",
        "matched_delivery_hours": int(len(df)),
        "first_delivery_hour": (
            df["deliveryHour"].min().strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "last_delivery_hour": (
            df["deliveryHour"].max().strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "decision_cutoff_assumption": DECISION_CUTOFF,
        "cutoff_status": "Provisional; confirm before final submission",
        "error_definition": (
            "forecastGeneration - actualGeneration; "
            "positive values indicate overforecasting"
        ),
        "actual_aggregation": (
            "Hourly mean of the two half-hourly actual observations, "
            "as implemented in the analysis pipeline"
        ),
    }


@app.get("/api/summary")
def get_summary():
    """Return overall forecast accuracy metrics."""

    df = load_analysis()
    metrics = calculate_metrics(df)

    return {
        **metrics,
        "coverage_percent": round(
            len(df) / (31 * 24) * 100,
            2,
        ),
        "period": "January 2026",
        "unit": "MW",
    }


@app.get("/api/forecasts")
def get_forecasts(
    start_date: str | None = Query(
        default=None,
        description="Start date in YYYY-MM-DD format",
    ),
    end_date: str | None = Query(
        default=None,
        description="End date in YYYY-MM-DD format",
    ),
    limit: int = Query(default=744, ge=1, le=744),
):
    """Return matched hourly forecasts and actual generation."""

    df = load_analysis()

    try:
        if start_date:
            start = pd.to_datetime(
                start_date,
                utc=True,
                errors="raise",
            )

            df = df[df["deliveryHour"] >= start]

        if end_date:
            # Include the entire specified end date.
            end = (
                pd.to_datetime(
                    end_date,
                    utc=True,
                    errors="raise",
                )
                + pd.Timedelta(days=1)
            )

            df = df[df["deliveryHour"] < end]

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Dates must be valid dates in YYYY-MM-DD format.",
        )

    df = df.head(limit)

    return {
        "count": int(len(df)),
        "unit": "MW",
        "data": serialize_records(df),
    }


@app.get("/api/forecasts/daily")
def get_daily_forecasts():
    """Aggregate hourly observations into daily summaries."""

    df = load_analysis()

    df["deliveryDate"] = (
        df["deliveryHour"].dt.strftime("%Y-%m-%d")
    )

    daily = (
        df.groupby("deliveryDate", as_index=False)
        .agg(
            averageForecastMW=("forecastGeneration", "mean"),
            averageActualMW=("actualGeneration", "mean"),
            maeMW=(
                "forecastError",
                lambda values: float(np.mean(np.abs(values))),
            ),
            biasMW=("forecastError", "mean"),
            deliveryHours=("deliveryHour", "count"),
        )
    )

    numeric_columns = [
        "averageForecastMW",
        "averageActualMW",
        "maeMW",
        "biasMW",
    ]

    daily[numeric_columns] = daily[numeric_columns].round(2)

    return {
        "count": int(len(daily)),
        "unit": "MW",
        "data": daily.to_dict(orient="records"),
    }



@app.get("/api/analysis")
def get_analysis():
    """Return summary metrics and the daily analysis together."""

    df = load_analysis()
    metrics = calculate_metrics(df)

    df["deliveryDate"] = (
        df["deliveryHour"].dt.strftime("%Y-%m-%d")
    )

    daily = (
        df.groupby("deliveryDate")
        .agg(
            averageForecastMW=("forecastGeneration", "mean"),
            averageActualMW=("actualGeneration", "mean"),
            maeMW=(
                "forecastError",
                lambda values: float(np.mean(np.abs(values))),
            ),
            biasMW=("forecastError", "mean"),
            deliveryHours=("deliveryHour", "count"),
        )
        .reset_index()
    )

    daily = daily.rename(columns={"deliveryDate": "date"})

    for column in [
        "averageForecastMW",
        "averageActualMW",
        "maeMW",
        "biasMW",
    ]:
        daily[column] = daily[column].round(2)

    return {
        "period": "January 2026",
        "metrics": metrics,
        "daily": daily.to_dict(orient="records"),
    }