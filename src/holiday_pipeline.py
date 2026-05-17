"""Load and ingest holiday reference data for calendar features."""

from pathlib import Path

import pandas as pd

from src.config import load_database_config
from src.database import create_tables, insert_holidays, open_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOLIDAY_CSV_PATH = PROJECT_ROOT / "data" / "reference" / "holidays_de_lu.csv"

HOLIDAY_COLUMNS = [
    "holiday_date",
    "holiday_name",
    "region",
    "is_nationwide",
    "source",
]


def load_holidays_csv(csv_path: Path = DEFAULT_HOLIDAY_CSV_PATH) -> pd.DataFrame:
    """Read, validate, and normalize the DE/LU holiday reference CSV."""
    holidays_df = pd.read_csv(csv_path)
    missing_columns = set(HOLIDAY_COLUMNS) - set(holidays_df.columns)

    if missing_columns:
        missing_column_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"Holiday CSV is missing columns: {missing_column_list}")

    holidays_df = holidays_df[HOLIDAY_COLUMNS].copy()
    holidays_df["holiday_date"] = pd.to_datetime(
        holidays_df["holiday_date"],
        errors="raise",
    ).dt.date
    holidays_df["holiday_name"] = holidays_df["holiday_name"].astype(str).str.strip()
    holidays_df["region"] = holidays_df["region"].astype(str).str.strip()
    holidays_df["is_nationwide"] = holidays_df["is_nationwide"].map(_parse_boolean)
    holidays_df["source"] = holidays_df["source"].where(
        holidays_df["source"].notna(),
        None,
    )

    if holidays_df.empty:
        raise ValueError("Holiday CSV contains no rows.")

    if holidays_df["holiday_name"].eq("").any():
        raise ValueError("Holiday CSV contains empty holiday_name values.")

    if holidays_df["region"].eq("").any():
        raise ValueError("Holiday CSV contains empty region values.")

    return holidays_df


def ingest_holidays(csv_path: Path = DEFAULT_HOLIDAY_CSV_PATH) -> int:
    """Load holiday reference rows into PostgreSQL and return the row count."""
    database_config = load_database_config()
    holidays_df = load_holidays_csv(csv_path)

    with open_connection(database_config) as connection:
        create_tables(connection)
        return insert_holidays(connection, holidays_df)


def _parse_boolean(value: object) -> bool:
    """Parse common CSV boolean representations into a Python bool."""
    if isinstance(value, bool):
        return value

    normalized_value = str(value).strip().lower()

    if normalized_value in {"true", "t", "1", "yes", "y"}:
        return True

    if normalized_value in {"false", "f", "0", "no", "n"}:
        return False

    raise ValueError(f"Cannot parse boolean value: {value}")
