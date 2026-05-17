"""Tests for SMARD API URL construction."""

from src.smard_client import SmardConfig, build_index_url, build_payload_url


def test_build_index_url_uses_configured_series_region_and_resolution():
    config = SmardConfig(smard_filter_id="4169", region="DE-LU", resolution="hour")

    result = build_index_url(config)

    assert result == "https://www.smard.de/app/chart_data/4169/DE-LU/index_hour.json"


def test_build_payload_url_uses_chunk_timestamp():
    config = SmardConfig(smard_filter_id="4169", region="DE-LU", resolution="hour")

    result = build_payload_url(config, 1735689600000)

    assert (
        result
        == "https://www.smard.de/app/chart_data/4169/DE-LU/4169_DE-LU_hour_1735689600000.json"
    )
