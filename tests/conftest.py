"""Shared pytest fixtures.

conftest.py is discovered automatically by pytest; fixtures defined here are
available to every test in this directory without being imported.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ridesim.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A test client bound to a freshly built application instance.

    TestClient drives the app through its real ASGI interface -- routing,
    validation, serialisation, and status-code selection all run exactly as
    they would under uvicorn. What it skips is the network: no socket is
    opened, so these tests are fast and cannot fail because a port was busy.

    Using create_app() rather than importing the module-level `app` gives each
    test a clean instance, so state added in a later phase (an in-memory driver
    store) cannot leak between tests.
    """
    with TestClient(create_app()) as test_client:
        yield test_client
