"""Environment selection and static endpoint constants.

Values are taken from the reverse-engineered app spec
(``resources/API_DOCUMENTATION.md`` §1). The base URL is chosen at runtime by the
selected :class:`Environment`; the image host is used to prefix relative image paths
returned by the API, and the upload URL is an absolute endpoint (not under ``/v1``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

#: Host that serves title/person/profile images. Relative image paths returned by the
#: API are resolved against this host (see ``models.base.resolve_image_url``).
IMAGE_HOST = "https://i.mydramalist.com"

#: Public website (not the API) — occasionally referenced for permalinks.
WEBSITE_URL = "https://mydramalist.com"

#: Absolute multipart upload endpoint. Not under the ``/v1`` base path.
UPLOAD_URL = "https://app-api.mydramalist.com/upload/bearer"

#: Default app version string sent in the ``version`` header. This mirrors the app the
#: spec was reconstructed from; override per-client if you emulate a different build.
DEFAULT_APP_VERSION = "2.3.3"

#: Environment variable names the client falls back to when arguments are omitted.
ENV_API_KEY = "MDL_API_KEY"
ENV_APP_VERSION = "MDL_APP_VERSION"
ENV_DEVICE_ID = "MDL_DEVICE_ID"


class Environment(str, Enum):
    """Selectable API environment. See spec §1."""

    PRODUCTION = "production"
    STAGING = "staging"

    @property
    def base_url(self) -> str:
        if self is Environment.STAGING:
            return "https://stagingv6api.mydramalist.com/v1"
        return "https://app-api.mydramalist.com/v1"


@dataclass(frozen=True)
class ClientConfig:
    """Immutable client configuration.

    ``api_key`` is the app's ``mdl-api-key`` header value. It is *not* shipped with this
    library (it is a runtime-initialized secret in the app); supply it explicitly or via
    the ``MDL_API_KEY`` environment variable. See ``docs/api-key-extraction.md``.
    """

    api_key: str
    app_version: str = DEFAULT_APP_VERSION
    environment: Environment = Environment.PRODUCTION
    device_id: str | None = None
    lang_code: str | None = None
    timeout: float = 30.0

    @property
    def base_url(self) -> str:
        return self.environment.base_url

    @classmethod
    def resolve(
        cls,
        api_key: str | None = None,
        *,
        app_version: str | None = None,
        environment: Environment = Environment.PRODUCTION,
        device_id: str | None = None,
        lang_code: str | None = None,
        timeout: float = 30.0,
    ) -> ClientConfig:
        """Build a config, falling back to environment variables where arguments are None."""
        key = api_key or os.environ.get(ENV_API_KEY)
        if not key:
            raise ValueError(
                "An mdl-api-key is required. Pass api_key=... or set the "
                f"{ENV_API_KEY} environment variable. See docs/api-key-extraction.md."
            )
        return cls(
            api_key=key,
            app_version=app_version or os.environ.get(ENV_APP_VERSION) or DEFAULT_APP_VERSION,
            environment=environment,
            device_id=device_id or os.environ.get(ENV_DEVICE_ID),
            lang_code=lang_code,
            timeout=timeout,
        )
