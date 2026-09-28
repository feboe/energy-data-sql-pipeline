"""PostgreSQL integration tests for continuous negative-price events."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.types.json import Jsonb

from src.config import load_database_config, load_env_file
from src.database import execute_sql_file, open_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
pytestmark = pytest.mark.integration


@pytest.fixture
def event_test_connection():
    """Provide a connection scoped to a temporary schema and always remove it."""
    load_env_file(PROJECT_ROOT / ".env")
    try:
        connection = open_connection(load_database_config())
    except (OSError, ValueError, psycopg.OperationalError) as error:
        pytest.fail(
            "PostgreSQL integration tests could not connect using the settings in "
            ".env. Start the local database (for example, `docker compose up -d`) "
            f"and verify its connection settings. Connection error: {error}"
        )

    schema_name = f"pytest_negative_price_events_{uuid4().hex}"
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}").format(sql.Identifier(schema_name))
            )
        connection.commit()

        execute_sql_file(connection, PROJECT_ROOT / "db" / "001_create_tables.sql")
        execute_sql_file(
            connection, PROJECT_ROOT / "db" / "003_create_analysis_views.sql"
        )
        yield connection
    finally:
        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema_name)
                )
            )
        connection.commit()
        connection.close()


def insert_day_ahead_prices(connection, observations):
    """Insert a minimal hourly day-ahead series into the isolated test schema."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO raw_imports (
                source_system, source_series_id, series_name, region, resolution,
                unit, chunk_timestamp_ms, chunk_timestamp, source_url, raw_payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                "pytest",
                "event-price",
                "day_ahead_price",
                "DE-LU",
                "hour",
                "EUR/MWh",
                0,
                datetime(2025, 1, 1, tzinfo=timezone.utc),
                "test://negative-price-events",
                Jsonb({}),
            ),
        )
        raw_import_id = cursor.fetchone()[0]
        cursor.executemany(
            """
            INSERT INTO measurements (
                raw_import_id, source_system, source_series_id, series_name, region,
                resolution, unit, observation_timestamp_ms, observation_timestamp, value
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    raw_import_id,
                    "pytest",
                    "event-price",
                    "day_ahead_price",
                    "DE-LU",
                    "hour",
                    "EUR/MWh",
                    int(observation_timestamp.timestamp() * 1000),
                    observation_timestamp,
                    price,
                )
                for observation_timestamp, price in observations
            ],
        )
    connection.commit()


def test_consecutive_negative_hours_form_one_event(event_test_connection):
    insert_day_ahead_prices(
        event_test_connection,
        [
            (datetime(2025, 1, 1, 0, tzinfo=timezone.utc), -1),
            (datetime(2025, 1, 1, 1, tzinfo=timezone.utc), -2),
            (datetime(2025, 1, 1, 2, tzinfo=timezone.utc), -3),
        ],
    )

    with event_test_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*), MAX(duration_hours) FROM negative_price_events")
        event_count, duration_hours = cursor.fetchone()

    assert event_count == 1
    assert duration_hours == 3


@pytest.mark.parametrize(
    "observations",
    [
        [
            (datetime(2025, 1, 1, 0, tzinfo=timezone.utc), -1),
            (datetime(2025, 1, 1, 1, tzinfo=timezone.utc), 1),
            (datetime(2025, 1, 1, 2, tzinfo=timezone.utc), -1),
        ],
        [
            (datetime(2025, 1, 1, 0, tzinfo=timezone.utc), -1),
            (datetime(2025, 1, 1, 2, tzinfo=timezone.utc), -1),
        ],
    ],
    ids=("positive-hour-between", "missing-hour-between"),
)
def test_positive_or_missing_intermediate_hour_splits_events(
    event_test_connection, observations
):
    insert_day_ahead_prices(event_test_connection, observations)

    with event_test_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM negative_price_events")
        event_count = cursor.fetchone()[0]

    assert event_count == 2


def test_new_year_event_stays_whole_in_its_start_year(event_test_connection):
    insert_day_ahead_prices(
        event_test_connection,
        [
            (datetime(2025, 12, 31, 21, tzinfo=timezone.utc), -1),
            (datetime(2025, 12, 31, 22, tzinfo=timezone.utc), -1),
            (datetime(2025, 12, 31, 23, tzinfo=timezone.utc), -1),
        ],
    )

    with event_test_connection.cursor() as cursor:
        cursor.execute("""
            SELECT start_year, duration_hours
            FROM negative_price_events
            """)
        event = cursor.fetchone()
        cursor.execute("""
            SELECT
                event_start_year,
                events_started_in_year,
                hours_in_events_started_in_year
            FROM yearly_negative_price_event_summary
            """)
        summary = cursor.fetchone()
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'yearly_negative_price_event_summary'
            """)
        summary_columns = {row[0] for row in cursor.fetchall()}

    assert event == (2025, 3)
    assert summary == (2025, 1, 3)
    assert {
        "event_start_year",
        "events_started_in_year",
        "hours_in_events_started_in_year",
        "avg_event_duration_hours_for_events_started_in_year",
        "median_event_duration_hours_for_events_started_in_year",
        "min_event_duration_hours_for_events_started_in_year",
        "max_event_duration_hours_for_events_started_in_year",
    } <= summary_columns
