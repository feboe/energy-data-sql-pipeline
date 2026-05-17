"""Database access helpers for schema setup and data ingestion."""

import psycopg
from pathlib import Path
from psycopg.types.json import Jsonb
from src.config import DatabaseConfig
import pandas as pd
from src.transform_smard import MEASUREMENT_COLUMNS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEW_SQL_FILES = (
    "002_create_quality_views.sql",
    "003_create_analysis_views.sql",
)


def open_connection(config: DatabaseConfig) -> psycopg.Connection:
    """Open a PostgreSQL connection from a database configuration."""
    return psycopg.connect(
        dbname=config.database,
        user=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
    )


def execute_sql_file(connection: psycopg.Connection, sql_file_path: Path) -> None:
    """Execute a SQL file inside the provided connection and commit it."""
    with open(sql_file_path, "r", encoding="utf-8") as file:
        sql_text = file.read()

    with connection.cursor() as cursor:
        cursor.execute(sql_text)
    connection.commit()


def create_tables(connection: psycopg.Connection) -> None:
    """Create the base database tables if they do not already exist."""
    sql_file_path = PROJECT_ROOT / "db" / "001_create_tables.sql"
    execute_sql_file(connection, sql_file_path)


def create_views(connection: psycopg.Connection) -> None:
    """Create or refresh the quality and analysis views."""
    for sql_file_name in VIEW_SQL_FILES:
        sql_file_path = PROJECT_ROOT / "db" / sql_file_name
        execute_sql_file(connection, sql_file_path)


def insert_raw_import(connection: psycopg.Connection, raw_import_record: dict) -> int:
    """Insert or find a raw import row and return its database id."""
    identity = (
        raw_import_record["source_system"],
        raw_import_record["source_series_id"],
        raw_import_record["region"],
        raw_import_record["resolution"],
        raw_import_record["chunk_timestamp_ms"],
    )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO raw_imports (
                source_system,
                source_series_id,
                series_name,
                region,
                resolution,
                unit,
                chunk_timestamp_ms,
                chunk_timestamp,
                source_url,
                raw_payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (
                source_system,
                source_series_id,
                region,
                resolution,
                chunk_timestamp_ms
            )
            DO NOTHING
            RETURNING id;
            """,
            (
                raw_import_record["source_system"],
                raw_import_record["source_series_id"],
                raw_import_record["series_name"],
                raw_import_record["region"],
                raw_import_record["resolution"],
                raw_import_record["unit"],
                raw_import_record["chunk_timestamp_ms"],
                raw_import_record["chunk_timestamp"],
                raw_import_record["source_url"],
                Jsonb(raw_import_record["raw_payload"]),
            ),
        )

        inserted_row = cursor.fetchone()

        if inserted_row is not None:
            connection.commit()
            return inserted_row[0]

        cursor.execute(
            """
            SELECT id
            FROM raw_imports
            WHERE source_system = %s
            AND source_series_id = %s
            AND region = %s
            AND resolution = %s
            AND chunk_timestamp_ms = %s;
            """,
            identity,
        )
        existing_row = cursor.fetchone()

    connection.commit()

    if existing_row is None:
        raise ValueError("Could not insert or find raw_import row.")

    return existing_row[0]


def insert_measurements(
    connection: psycopg.Connection, measurements_df: pd.DataFrame
) -> int:
    """Insert normalized measurements and return the number of inserted rows."""
    cols = MEASUREMENT_COLUMNS
    records = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in measurements_df[cols].itertuples(index=False, name=None)
    ]

    if not records:
        return 0

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO measurements (
                raw_import_id,
                source_system,
                source_series_id,
                series_name,
                region,
                resolution,
                unit,
                observation_timestamp_ms,
                observation_timestamp,
                value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (
                source_system,
                source_series_id,
                region,
                resolution,
                observation_timestamp_ms
            )
            DO NOTHING;
            """,
            records,
        )
        inserted_row_count = cursor.rowcount
    connection.commit()
    return inserted_row_count


def insert_holidays(connection: psycopg.Connection, holidays_df: pd.DataFrame) -> int:
    """Upsert holiday rows and return the number of input records processed."""
    cols = [
        "holiday_date",
        "holiday_name",
        "region",
        "is_nationwide",
        "source",
    ]
    records = [
        tuple(None if pd.isna(value) else value for value in row)
        for row in holidays_df[cols].itertuples(index=False, name=None)
    ]

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO holidays (
                holiday_date,
                holiday_name,
                region,
                is_nationwide,
                source
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (holiday_date, region, holiday_name)
            DO UPDATE SET
                is_nationwide = EXCLUDED.is_nationwide,
                source = EXCLUDED.source;
            """,
            records,
        )
    connection.commit()
    return len(records)
