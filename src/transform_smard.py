from datetime import datetime, timezone
import pandas as pd
from src.smard_client import SmardConfig

SOURCE_SYSTEM = "SMARD"
HOURLY_MEASUREMENT_COLUMNS = [
    "raw_import_id",
    "source_system",
    "series_name",
    "smard_filter_id",
    "region",
    "resolution",
    "observation_timestamp_ms",
    "observation_timestamp",
    "value",
]


def timestamp_ms_to_datetime(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)


def build_raw_import_record(
    config: SmardConfig,
    timestamp: int,
    payload: dict,
    series_name: str,
    source_url: str,
) -> dict:
    timestamp_dt = timestamp_ms_to_datetime(timestamp)
    return {
        "source_system": SOURCE_SYSTEM,
        "series_name": series_name,
        "smard_filter_id": config.smard_filter_id,
        "region": config.region,
        "resolution": config.resolution,
        "chunk_timestamp_ms": timestamp,
        "chunk_timestamp": timestamp_dt,
        "source_url": source_url,
        "raw_payload": payload,
    }


def extract_hourly_measurements(
    payload: dict,
    raw_import_id: int,
    config: SmardConfig,
    series_name: str,
) -> pd.DataFrame:

    if "series" not in payload:
        raise ValueError("Payload does not contain 'series' key")

    df = pd.DataFrame(payload["series"], columns=["observation_timestamp_ms", "value"])
    df["raw_import_id"] = raw_import_id
    df["source_system"] = SOURCE_SYSTEM
    df["series_name"] = series_name
    df["smard_filter_id"] = config.smard_filter_id
    df["region"] = config.region
    df["resolution"] = config.resolution
    df["observation_timestamp"] = df["observation_timestamp_ms"].apply(
        timestamp_ms_to_datetime
    )
    return df[HOURLY_MEASUREMENT_COLUMNS]
