"""Async transport. The unasync-generated sync twin lives at ``mdl._sync._transport``."""

from __future__ import annotations

import json as _jsonlib
from typing import Any, Optional, cast

from curl_cffi.requests import Session

from .._request import (
    PreparedRequest,
    TransportResponse,
    build_headers,
    clean_params,
    extract_error_message,
)
from ..auth import InMemoryTokenStore, TokenStore
from ..config import ClientConfig
from ..errors import error_for_status


class SyncTransport:
    """Executes :class:`PreparedRequest` objects against the API.

    By default it owns a :class:`curl_cffi.requests.AsyncSession` that impersonates a real
    browser/mobile TLS fingerprint (``config.impersonate``) so requests clear Cloudflare's
    bot challenge — a stock Python TLS stack is served a 403 and never reaches the API. Any
    requests-compatible client (e.g. ``httpx.AsyncClient`` in tests) may be injected instead;
    only ``.request()`` and the response's ``.status_code`` / ``.text`` / ``.headers`` are
    used. On a 401 the stored bearer token is cleared before the error is raised, mirroring
    the app's behaviour.
    """

    def __init__(
        self,
        config: ClientConfig,
        token_store: Optional[TokenStore] = None,
        *,
        client: Optional[Any] = None,
    ) -> None:
        self._config = config
        self.tokens: TokenStore = token_store or InMemoryTokenStore()
        # Typed Any: the transport accepts any requests-compatible client (curl_cffi or an
        # injected httpx client). curl_cffi types ``impersonate`` as a Literal of known
        # fingerprint names; we allow any string so new targets work without a lib bump.
        self._client: Any = client or Session(
            timeout=config.timeout, impersonate=cast(Any, config.impersonate)
        )
        self._owns_client = client is None

    @property
    def config(self) -> ClientConfig:
        return self._config

    def request(self, prepared: PreparedRequest) -> TransportResponse:
        token = self.tokens.get_token() if prepared.auth else None
        headers = build_headers(
            self._config,
            token,
            auth=prepared.auth,
            multipart=prepared.multipart,
        )
        url = prepared.url(self._config.base_url)

        kwargs: dict[str, Any] = {"headers": headers}
        params = clean_params(prepared.params)
        if params is not None:
            kwargs["params"] = params
        if prepared.multipart:
            if prepared.files:
                kwargs["files"] = prepared.files
            if prepared.data:
                kwargs["data"] = prepared.data
        elif prepared.json is not None:
            kwargs["json"] = prepared.json

        response = self._client.request(prepared.method, url, **kwargs)
        return self._process(response, url)

    def _process(self, response: Any, url: str) -> TransportResponse:
        text = response.text
        parsed: Any = None
        if text:
            try:
                parsed = _jsonlib.loads(text)
            except ValueError:
                parsed = None

        if response.status_code >= 400:
            if response.status_code == 401:
                self.tokens.clear()
            message = extract_error_message(parsed if parsed is not None else text)
            raise error_for_status(
                response.status_code, message, body=parsed if parsed is not None else text, url=url
            )

        return TransportResponse(
            status_code=response.status_code,
            json=parsed,
            text=text,
            headers=dict(response.headers),
            url=url,
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "SyncTransport":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
