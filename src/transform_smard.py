"""Transform SMARD API payloads into database-ready records."""

from datetime import datetime, timezone

import pandas as pd

from src.smard_client import SmardConfig

SOURCE_SYSTEM = "SMARD"
MEASUREMENT_COLUMNS = [
    "raw_import_id",
    "source_system",
    "source_series_id",
    "series_name",
    "region",
    "resolution",
    "unit",
    "observation_timestamp_ms",
    "observation_timestamp",
    "value",
]


def timestamp_ms_to_datetime(timestamp: int) -> datetime:
    """Convert a Unix timestamp in milliseconds to a UTC datetime."""
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def build_raw_import_record(
    config: SmardConfig,
    timestamp: int,
    payload: dict,
    series_name: str,
    unit: str,
    source_url: str,
) -> dict:
    """Build the raw import metadata row for a fetched SMARD payload."""
    timestamp_dt = timestamp_ms_to_datetime(timestamp)
    return {
        "source_system": SOURCE_SYSTEM,
        "source_series_id": config.smard_filter_id,
        "series_name": series_name,
        "region": config.region,
        "resolution": config.resolution,
        "unit": unit,
        "chunk_timestamp_ms": timestamp,
        "chunk_timestamp": timestamp_dt,
        "source_url": source_url,
        "raw_payload": payload,
    }


def extract_measurements(
    payload: dict,
    raw_import_id: int,
    config: SmardConfig,
    series_name: str,
    unit: str,
) -> pd.DataFrame:
    """Extract normalized measurement rows from a SMARD payload."""

    if "series" not in payload:
        raise ValueError("Payload does not contain 'series' key")

    df = pd.DataFrame(payload["series"], columns=["observation_timestamp_ms", "value"])
    df["raw_import_id"] = raw_import_id
    df["source_system"] = SOURCE_SYSTEM
    df["source_series_id"] = config.smard_filter_id
    df["series_name"] = series_name
    df["region"] = config.region
    df["resolution"] = config.resolution
    df["unit"] = unit
    df["observation_timestamp"] = df["observation_timestamp_ms"].apply(
        timestamp_ms_to_datetime
    )
    return df[MEASUREMENT_COLUMNS]
