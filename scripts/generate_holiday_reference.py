"""Generate the DE/LU holiday reference CSV used by the pipeline."""

from pathlib import Path

import holidays
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "reference" / "holidays_de_lu.csv"
DEFAULT_START_YEAR = 2020
DEFAULT_END_YEAR = 2026


def build_holiday_dataframe(start_year: int, end_year: int) -> pd.DataFrame:
    """Build a sorted holiday reference DataFrame for Germany and Luxembourg."""
    rows = []

    de_holidays = holidays.country_holidays(
        "DE",
        years=range(start_year, end_year + 1),
    )
    for holiday_date, holiday_name in de_holidays.items():
        rows.append(
            {
                "holiday_date": holiday_date,
                "holiday_name": holiday_name,
                "region": "DE",
                "is_nationwide": True,
                "source": "python-holidays",
            }
        )

    lu_holidays = holidays.country_holidays(
        "LU",
        years=range(start_year, end_year + 1),
    )
    for holiday_date, holiday_name in lu_holidays.items():
        rows.append(
            {
                "holiday_date": holiday_date,
                "holiday_name": holiday_name,
                "region": "LU",
                "is_nationwide": True,
                "source": "python-holidays",
            }
        )

    holidays_df = pd.DataFrame(rows)
    return holidays_df.sort_values(
        ["holiday_date", "region", "holiday_name"],
    ).reset_index(drop=True)


if __name__ == "__main__":
    df = build_holiday_dataframe(DEFAULT_START_YEAR, DEFAULT_END_YEAR)

    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DEFAULT_OUTPUT_PATH, index=False)

    print(df.head())
    print(f"Wrote {len(df)} holiday rows to {DEFAULT_OUTPUT_PATH}")
