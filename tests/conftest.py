"""Shared pytest fixtures.

Ensures the ``src`` layout is importable without an editable install, and provides
respx-mocked sync/async clients that talk to the production base URL.

The production transport uses ``curl_cffi`` (to clear Cloudflare's TLS fingerprinting),
which ``respx`` cannot intercept. The tests exercise request construction and response
parsing, not the real network, so the fixtures inject an ``httpx`` client instead — the
transport is client-agnostic, and ``respx`` mocks httpx.
"""

from __future__ import annotations

import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from mdl import AsyncMDLClient, MDLClient  # noqa: E402
from mdl.config import Environment  # noqa: E402

BASE_URL = Environment.PRODUCTION.base_url
API_KEY = "test-api-key"


@pytest.fixture
def sync_client() -> MDLClient:
    http_client = httpx.Client()
    client = MDLClient(api_key=API_KEY, app_version="2.3.3", http_client=http_client)
    yield client
    client.close()
    http_client.close()


@pytest.fixture
async def async_client() -> AsyncMDLClient:
    http_client = httpx.AsyncClient()
    client = AsyncMDLClient(api_key=API_KEY, app_version="2.3.3", http_client=http_client)
    yield client
    await client.aclose()
    await http_client.aclose()
