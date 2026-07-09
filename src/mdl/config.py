"""Environment selection and static endpoint constants.

Values are taken from the reverse-engineered app spec
(``resources/API_DOCUMENTATION.md`` §1). The base URL is chosen at runtime by the
selected :class:`Environment`; the image host is used to prefix relative image paths
returned by the API, and the upload URL is an absolute endpoint (not under ``/v1``).
"""

from __future__ import annotations

import os
import secrets
import string
from dataclasses import dataclass
from enum import Enum

#: Character set and length of the ``mdl-api-key``. Reverse engineering shows the app fills
#: this header with ``Utils.getRandomString()`` — 20 characters drawn from ``[a-zA-Z0-9]`` via
#: a secure RNG, regenerated on every launch. The server does not validate it (requests
#: succeed even with the header omitted), so it is a client-generated nonce, not a secret.
_API_KEY_ALPHABET = string.ascii_letters + string.digits
_API_KEY_LENGTH = 20


def generate_api_key() -> str:
    """Generate an ``mdl-api-key`` the way the app does: 20 random ``[a-zA-Z0-9]`` chars."""
    return "".join(secrets.choice(_API_KEY_ALPHABET) for _ in range(_API_KEY_LENGTH))

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

#: Default TLS/HTTP2 fingerprint the transport impersonates to clear Cloudflare bot
#: protection. Production rejects a stock Python TLS stack with a 403 challenge; a real
#: browser/mobile fingerprint passes. Any curl_cffi ``impersonate`` target works — see
#: https://github.com/lexiforest/curl_cffi for the list.
DEFAULT_IMPERSONATE = "chrome"

#: Environment variable names the client falls back to when arguments are omitted.
ENV_API_KEY = "MDL_API_KEY"
ENV_APP_VERSION = "MDL_APP_VERSION"
ENV_DEVICE_ID = "MDL_DEVICE_ID"
ENV_IMPERSONATE = "MDL_IMPERSONATE"


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

    ``api_key`` is the ``mdl-api-key`` header value. Despite the name it is not a secret:
    the app generates a fresh random 20-char string on each launch and the server does not
    validate it. If you do not supply one, :meth:`resolve` generates a valid key for you.
    """

    api_key: str
    app_version: str = DEFAULT_APP_VERSION
    environment: Environment = Environment.PRODUCTION
    device_id: str | None = None
    lang_code: str | None = None
    timeout: float = 30.0
    impersonate: str = DEFAULT_IMPERSONATE

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
        impersonate: str | None = None,
    ) -> ClientConfig:
        """Build a config, falling back to environment variables where arguments are None.

        The ``mdl-api-key`` is a client-generated nonce, not a secret (see the class
        docstring), so when none is supplied — via argument or ``MDL_API_KEY`` — a fresh
        valid key is generated automatically.
        """
        key = api_key or os.environ.get(ENV_API_KEY) or generate_api_key()
        return cls(
            api_key=key,
            app_version=app_version or os.environ.get(ENV_APP_VERSION) or DEFAULT_APP_VERSION,
            environment=environment,
            device_id=device_id or os.environ.get(ENV_DEVICE_ID),
            lang_code=lang_code,
            timeout=timeout,
            impersonate=impersonate or os.environ.get(ENV_IMPERSONATE) or DEFAULT_IMPERSONATE,
        )
