from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from src.config import load_database_config
from src.database import (
    create_tables,
    insert_hourly_measurements,
    insert_raw_import,
    open_connection,
)
from src.smard_catalog import SmardSeries
from src.smard_client import build_payload_url, get_payload, get_timestamps
from src.transform_smard import (
    build_raw_import_record,
    extract_hourly_measurements,
    timestamp_ms_to_datetime,
)


LOCAL_TIMEZONE = ZoneInfo("Europe/Berlin")


def normalize_datetime_to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=LOCAL_TIMEZONE)

    return value.astimezone(timezone.utc)


def filter_chunk_timestamps(
    available_timestamps: list[int],
    start_date: datetime,
    end_date: datetime | None = None,
) -> list[int]:
    start_utc = normalize_datetime_to_utc(start_date)
    end_utc = normalize_datetime_to_utc(end_date) if end_date is not None else None

    if end_utc is not None and end_utc < start_utc:
        raise ValueError("end_date must be greater than or equal to start_date.")

    sorted_timestamps = sorted(available_timestamps)
    selected_timestamps: list[int] = []

    for index, timestamp_ms in enumerate(sorted_timestamps):
        chunk_start = timestamp_ms_to_datetime(timestamp_ms)
        next_chunk_start = None

        if index + 1 < len(sorted_timestamps):
            next_chunk_start = timestamp_ms_to_datetime(sorted_timestamps[index + 1])

        overlaps_start = next_chunk_start is None or next_chunk_start > start_utc
        overlaps_end = end_utc is None or chunk_start <= end_utc

        if overlaps_start and overlaps_end:
            selected_timestamps.append(timestamp_ms)

    return selected_timestamps


def filter_hourly_measurements_for_period(
    hourly_measurements_df: pd.DataFrame,
    start_date: datetime,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    start_utc = normalize_datetime_to_utc(start_date)
    mask = hourly_measurements_df["observation_timestamp"] >= start_utc

    if end_date is not None:
        end_utc = normalize_datetime_to_utc(end_date)
        mask &= hourly_measurements_df["observation_timestamp"] <= end_utc

    return hourly_measurements_df.loc[mask].reset_index(drop=True)


def ingest_smard_series(
    series: SmardSeries,
    start_date: datetime,
    end_date: datetime | None = None,
) -> dict[str, int]:
    database_config = load_database_config()
    available_timestamps = get_timestamps(series.config)
    selected_timestamps = filter_chunk_timestamps(
        available_timestamps=available_timestamps,
        start_date=start_date,
        end_date=end_date,
    )

    processed_chunk_count = 0
    hourly_row_count = 0

    with open_connection(database_config) as connection:
        create_tables(connection)

        for timestamp_ms in selected_timestamps:
            payload = get_payload(series.config, timestamp_ms)
            source_url = build_payload_url(series.config, timestamp_ms)
            raw_import_record = build_raw_import_record(
                config=series.config,
                timestamp=timestamp_ms,
                payload=payload,
                series_name=series.series_name,
                source_url=source_url,
            )
            raw_import_id = insert_raw_import(connection, raw_import_record)

            hourly_measurements_df = extract_hourly_measurements(
                payload=payload,
                raw_import_id=raw_import_id,
                config=series.config,
                series_name=series.series_name,
            )
            filtered_hourly_measurements_df = filter_hourly_measurements_for_period(
                hourly_measurements_df=hourly_measurements_df,
                start_date=start_date,
                end_date=end_date,
            )

            if not filtered_hourly_measurements_df.empty:
                insert_hourly_measurements(connection, filtered_hourly_measurements_df)
                hourly_row_count += len(filtered_hourly_measurements_df)

            processed_chunk_count += 1

    return {
        "processed_chunk_count": processed_chunk_count,
        "hourly_row_count": hourly_row_count,
        "selected_chunk_count": len(selected_timestamps),
    }
