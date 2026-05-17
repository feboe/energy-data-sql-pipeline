"""Tests for SMARD ingestion time handling."""

from datetime import datetime, timezone

import pandas as pd

from src.smard_pipeline import (
    filter_chunk_timestamps,
    filter_measurements_for_period,
    normalize_datetime_to_utc,
)


def timestamp_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def test_naive_datetime_is_interpreted_as_berlin_time():
    result = normalize_datetime_to_utc(datetime(2025, 1, 1, 1, 0))

    assert result == datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_filter_chunk_timestamps_selects_overlapping_chunks():
    available_timestamps = [
        timestamp_ms(datetime(2025, 1, 1, tzinfo=timezone.utc)),
        timestamp_ms(datetime(2025, 1, 8, tzinfo=timezone.utc)),
        timestamp_ms(datetime(2025, 1, 15, tzinfo=timezone.utc)),
    ]

    result = filter_chunk_timestamps(
        available_timestamps=available_timestamps,
        start_date=datetime(2025, 1, 3, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 10, tzinfo=timezone.utc),
    )

    assert result == available_timestamps[:2]


def test_filter_measurements_for_period_uses_inclusive_bounds():
    measurements_df = pd.DataFrame(
        {
            "observation_timestamp": [
                datetime(2024, 12, 31, 23, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 0, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
                datetime(2025, 1, 1, 2, tzinfo=timezone.utc),
            ],
            "value": [10, 20, 30, 40],
        }
    )

    result = filter_measurements_for_period(
        measurements_df=measurements_df,
        start_date=datetime(2025, 1, 1, 0, tzinfo=timezone.utc),
        end_date=datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
    )

    assert result["value"].tolist() == [20, 30]
