"""Tests for holiday reference parsing and validation."""

from datetime import date

import pytest

from src.holiday_pipeline import _parse_boolean, load_holidays_csv


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("true", True),
        ("yes", True),
        ("1", True),
        ("false", False),
        ("no", False),
        ("0", False),
    ],
)
def test_parse_boolean_accepts_common_csv_values(raw_value, expected):
    assert _parse_boolean(raw_value) is expected


def test_load_holidays_csv_normalizes_expected_columns(tmp_path):
    csv_path = tmp_path / "holidays.csv"
    csv_path.write_text(
        "\n".join(
            [
                "holiday_date,holiday_name,region,is_nationwide,source",
                "2025-01-01, New Year's Day ,DE,true,python-holidays",
            ]
        ),
        encoding="utf-8",
    )

    result = load_holidays_csv(csv_path)

    assert result.loc[0, "holiday_date"] == date(2025, 1, 1)
    assert result.loc[0, "holiday_name"] == "New Year's Day"
    assert result.loc[0, "region"] == "DE"
    assert bool(result.loc[0, "is_nationwide"]) is True


def test_load_holidays_csv_rejects_missing_columns(tmp_path):
    csv_path = tmp_path / "holidays.csv"
    csv_path.write_text("holiday_date,holiday_name\n2025-01-01,New Year's Day\n")

    with pytest.raises(ValueError, match="missing columns"):
        load_holidays_csv(csv_path)
