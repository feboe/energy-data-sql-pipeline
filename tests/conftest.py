"""Pytest configuration for keeping the default test run database-free."""

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless the caller explicitly selects a marker."""
    if config.option.markexpr:
        return

    skip_integration = pytest.mark.skip(
        reason="PostgreSQL integration test; run with: python -m pytest -m integration"
    )
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip_integration)
