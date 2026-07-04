"""Shared pytest fixtures.

Ensures the ``src`` layout is importable without an editable install, and provides
respx-mocked sync/async clients that talk to the production base URL.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from mdl import AsyncMDLClient, MDLClient  # noqa: E402
from mdl.config import Environment  # noqa: E402

BASE_URL = Environment.PRODUCTION.base_url
API_KEY = "test-api-key"


@pytest.fixture
def sync_client() -> MDLClient:
    client = MDLClient(api_key=API_KEY, app_version="2.3.3")
    yield client
    client.close()


@pytest.fixture
async def async_client() -> AsyncMDLClient:
    client = AsyncMDLClient(api_key=API_KEY, app_version="2.3.3")
    yield client
    await client.aclose()
