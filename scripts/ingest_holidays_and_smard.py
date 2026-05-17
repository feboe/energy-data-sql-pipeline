from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_database_config, load_env_file
from src.database import create_views, open_connection
from src.holiday_pipeline import ingest_holidays
from src.smard_catalog import SMARD_SERIES_CATALOG
from src.smard_pipeline import ingest_smard_series_batch

HOLIDAY_CSV_PATH = PROJECT_ROOT / "data" / "reference" / "holidays_de_lu.csv"
START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2025, 12, 31, 23)
SMARD_SERIES_BATCH = SMARD_SERIES_CATALOG


def main() -> None:
    load_env_file(PROJECT_ROOT / ".env")

    holiday_row_count = ingest_holidays(HOLIDAY_CSV_PATH)
    print(f"Ingested {holiday_row_count} holiday rows.")

    results = ingest_smard_series_batch(
        series_batch=SMARD_SERIES_BATCH,
        start_date=START_DATE,
        end_date=END_DATE,
    )

    for series_name, result in results.items():
        print(
            f"{series_name}: "
            f"{result['measurement_row_count']} rows, "
            f"{result['processed_chunk_count']} chunks."
        )

    database_config = load_database_config()
    with open_connection(database_config) as connection:
        create_views(connection)

    print("Recreated views.")


if __name__ == "__main__":
    main()
