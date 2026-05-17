"""Tests for transforming SMARD payloads into normalized records."""

from datetime import datetime, timezone

import pytest

from src.smard_client import SmardConfig
from src.transform_smard import (
    MEASUREMENT_COLUMNS,
    extract_measurements,
    timestamp_ms_to_datetime,
)


def test_timestamp_ms_to_datetime_returns_utc_datetime():
    result = timestamp_ms_to_datetime(1735689600000)

    assert result == datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_extract_measurements_adds_series_metadata():
    payload = {"series": [[1735689600000, 42.5], [1735693200000, None]]}
    config = SmardConfig(smard_filter_id="4169", region="DE-LU", resolution="hour")

    result = extract_measurements(
        payload=payload,
        raw_import_id=7,
        config=config,
        series_name="day_ahead_price",
        unit="EUR/MWh",
    )

    assert result.columns.tolist() == MEASUREMENT_COLUMNS
    assert result["raw_import_id"].tolist() == [7, 7]
    assert result["source_series_id"].tolist() == ["4169", "4169"]
    assert result["series_name"].tolist() == ["day_ahead_price", "day_ahead_price"]
    assert result["region"].tolist() == ["DE-LU", "DE-LU"]
    assert result["unit"].tolist() == ["EUR/MWh", "EUR/MWh"]
    assert result.loc[0, "observation_timestamp"] == datetime(
        2025, 1, 1, tzinfo=timezone.utc
    )


def test_extract_measurements_requires_series_key():
    config = SmardConfig(smard_filter_id="4169", region="DE-LU", resolution="hour")

    with pytest.raises(ValueError, match="series"):
        extract_measurements(
            payload={},
            raw_import_id=7,
            config=config,
            series_name="day_ahead_price",
            unit="EUR/MWh",
        )
