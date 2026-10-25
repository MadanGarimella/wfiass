import pandas as pd
import pytest

from analyze_forecasts import (
    calculate_metrics,
    select_latest_forecasts,
)


def test_calculate_metrics():
    """Metrics should use signed errors and absolute errors correctly."""
    df = pd.DataFrame({
        "forecastGeneration": [110.0, 180.0, 330.0],
        "actualGeneration": [100.0, 200.0, 300.0],
    })

    result = calculate_metrics(df)

    assert result["matched_hours"] == 3
    assert result["mae"] == pytest.approx(20.0)
    assert result["rmse"] == pytest.approx(21.6)
    assert result["bias"] == pytest.approx(6.67, abs=0.01)


def test_calculate_metrics_empty_dataframe():
    """An empty dataset should not produce misleading metrics."""
    df = pd.DataFrame()

    assert calculate_metrics(df) is None


def test_select_latest_forecast_before_cutoff():
    """Choose the latest forecast published before the cutoff."""
    forecasts = pd.DataFrame({
        "deliveryHour": pd.to_datetime([
            "2026-01-01T10:00:00Z",
            "2026-01-01T10:00:00Z",
        ], utc=True),
        "publishTime": pd.to_datetime([
            "2025-12-31T20:00:00Z",
            "2025-12-31T22:30:00Z",
        ], utc=True),
        "forecastGeneration": [10000.0, 12000.0],
    })

    selected = select_latest_forecasts(forecasts)

    assert len(selected) == 1
    assert selected.iloc[0]["forecastGeneration"] == 12000.0


def test_forecast_published_after_cutoff_is_excluded():
    """Forecasts published after 23:00 UTC the previous day are excluded."""
    forecasts = pd.DataFrame({
        "deliveryHour": pd.to_datetime([
            "2026-01-01T10:00:00Z",
        ], utc=True),
        "publishTime": pd.to_datetime([
            "2025-12-31T23:30:00Z",
        ], utc=True),
        "forecastGeneration": [12000.0],
    })

    selected = select_latest_forecasts(forecasts)

    assert selected.empty


def test_forecast_selection_keeps_latest_eligible_publication():
    """Later eligible publications should replace earlier ones."""
    forecasts = pd.DataFrame({
        "deliveryHour": pd.to_datetime([
            "2026-01-01T10:00:00Z",
            "2026-01-01T10:00:00Z",
            "2026-01-01T10:00:00Z",
        ], utc=True),
        "publishTime": pd.to_datetime([
            "2025-12-31T18:00:00Z",
            "2025-12-31T21:00:00Z",
            "2025-12-31T23:30:00Z",
        ], utc=True),
        "forecastGeneration": [10000.0, 11000.0, 13000.0],
    })

    selected = select_latest_forecasts(forecasts)

    assert len(selected) == 1
    assert selected.iloc[0]["forecastGeneration"] == 11000.0
