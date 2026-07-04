"""mdl (pymdl) — a fully-typed sync + async Python client for the MyDramaList app API.

Quick start::

    from mdl import MDLClient

    with MDLClient(api_key="...") as client:
        title = client.titles.get_title(686)
        print(title.title)

    # async
    from mdl import AsyncMDLClient

    async with AsyncMDLClient(api_key="...") as client:
        title = await client.titles.get_title(686)

The ``mdl-api-key`` is not shipped with this library; supply it via ``api_key=`` or the
``MDL_API_KEY`` environment variable (see ``docs/api-key-extraction.md``).
"""

from __future__ import annotations

from ._async.client import MDLClient as AsyncMDLClient
from ._sync.client import MDLClient
from ._version import __version__
from .auth import FileTokenStore, InMemoryTokenStore, TokenStore
from .config import ClientConfig, Environment
from .errors import (
    MDLAuthError,
    MDLConfigError,
    MDLError,
    MDLForbiddenError,
    MDLNetworkError,
    MDLNotFoundError,
    MDLRateLimitedError,
    MDLServerError,
)
from .pagination import Page

__all__ = [
    "__version__",
    "MDLClient",
    "AsyncMDLClient",
    "ClientConfig",
    "Environment",
    "Page",
    "TokenStore",
    "InMemoryTokenStore",
    "FileTokenStore",
    "MDLError",
    "MDLConfigError",
    "MDLNetworkError",
    "MDLAuthError",
    "MDLForbiddenError",
    "MDLNotFoundError",
    "MDLRateLimitedError",
    "MDLServerError",
]
