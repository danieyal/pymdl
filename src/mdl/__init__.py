"""mdl — a fully-typed sync + async Python client for the MyDramaList app API.

Quick start::

    from mdl import MDLClient

    with MDLClient() as client:
        title = client.titles.get_title(686)
        print(title.title)

    # async
    from mdl import AsyncMDLClient

    async with AsyncMDLClient() as client:
        title = await client.titles.get_title(686)

The ``mdl-api-key`` is a client-generated nonce, not a secret; one is generated automatically
when not supplied. Pin it via ``api_key=`` or ``MDL_API_KEY`` only if you want reproducible
requests (see ``docs/api-key-extraction.md``).
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
