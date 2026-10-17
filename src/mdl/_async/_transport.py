"""Async transport. The unasync-generated sync twin lives at ``mdl._sync._transport``."""

from __future__ import annotations

import json as _jsonlib
from asyncio import Lock
from typing import Any, Optional, cast

from curl_cffi.requests import AsyncSession

from .._request import (
    PreparedRequest,
    TransportResponse,
    build_headers,
    clean_params,
    extract_error_message,
)
from ..auth import InMemoryTokenStore, TokenStore
from ..config import ClientConfig
from ..errors import MDLAuthError, MDLConfigError, MDLError, error_for_status
from ..models.auth import AuthResponse


class AsyncTransport:
    """Executes :class:`PreparedRequest` objects against the API.

    By default it owns a ``curl_cffi`` session (``curl_cffi.requests.Session`` /
    ``AsyncSession``) that impersonates a real browser/mobile TLS fingerprint
    (``config.impersonate``) so requests clear Cloudflare's bot challenge — a stock Python
    TLS stack is served a 403 and never reaches the API. Any requests-compatible client (an
    injected ``httpx`` client in tests, for example) may be supplied instead; only
    ``.request()`` and the response's ``.status_code`` / ``.text`` / ``.headers`` are used.

    On a 401 for a request that carried a bearer token, the transport exchanges the stored
    refresh token for a new token pair once and retries. If there is no refresh token, the
    refresh fails, or the retry is also rejected, the stored tokens are cleared before the
    error is raised, mirroring the app's behaviour.
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
        self._client: Any = client or AsyncSession(
            timeout=config.timeout, impersonate=cast(Any, config.impersonate)
        )
        self._owns_client = client is None

    @property
    def config(self) -> ClientConfig:
        return self._config

    async def request(self, prepared: PreparedRequest) -> TransportResponse:
        token = self.tokens.get_token() if prepared.auth else None
        response = await self._send(prepared, token)
        if (
            response.status_code == 401
            and token is not None
            and await self._refresh_after_401(token)
        ):
            token = self.tokens.get_token()
            response = await self._send(prepared, token)
        return self._process(
            response, prepared.url(self._config.base_url), authenticated=token is not None
        )

    async def refresh(self, refresh_token: Optional[str] = None) -> AuthResponse:
        """``POST /auth/refresh`` — swap a refresh token for a new token pair and store it.

        Uses the stored refresh token unless one is given. Raises
        :class:`~mdl.errors.MDLAuthError` when the server rejects it.
        """
        token = refresh_token or self.tokens.get_refresh_token()
        if not token:
            raise MDLConfigError("No refresh token is stored; call auth.login() first")
        resp = await self.request(
            PreparedRequest("POST", "/auth/refresh", json={"refresh_token": token}, auth=False)
        )
        data = resp.json
        if not isinstance(data, dict) or not data.get("access_token"):
            # The OAuth2 server reports a rejected refresh token with HTTP 200 and an
            # ``error`` / ``error_description`` body.
            message = (
                data.get("error_description") if isinstance(data, dict) else None
            ) or extract_error_message(data)
            raise MDLAuthError(message, status_code=resp.status_code, body=data, url=resp.url)
        auth = AuthResponse.model_validate(data)
        self.tokens.set_token(auth.access_token)
        if auth.refresh_token:
            self.tokens.set_refresh_token(auth.refresh_token)
        return auth

    async def _refresh_after_401(self, failed_token: str) -> bool:
        """Refresh the token pair after ``failed_token`` got a 401. Returns whether to retry."""
        # Created on first use so an async lock binds to the running event loop (Python 3.9
        # binds it at creation). dict.setdefault is atomic, so threads using the sync
        # client always share one lock.
        lock: Lock = self.__dict__.setdefault("_refresh_lock", Lock())
        async with lock:
            current = self.tokens.get_token()
            if current is not None and current != failed_token:
                # Another request refreshed the pair while this one waited for the lock.
                return True
            if not self.tokens.get_refresh_token():
                return False
            try:
                await self.refresh()
            except MDLError:
                return False
            return True

    async def _send(self, prepared: PreparedRequest, token: Optional[str]) -> Any:
        headers = build_headers(
            self._config,
            token,
            auth=prepared.auth,
            multipart=prepared.multipart,
        )
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

        return await self._client.request(
            prepared.method, prepared.url(self._config.base_url), **kwargs
        )

    def _process(
        self, response: Any, url: str, *, authenticated: bool = True
    ) -> TransportResponse:
        text = response.text
        parsed: Any = None
        if text:
            try:
                parsed = _jsonlib.loads(text)
            except ValueError:
                parsed = None

        if response.status_code >= 400:
            if response.status_code == 401 and authenticated:
                # Only a rejected bearer token is stale; an anonymous 401 (a refresh or
                # social login) leaves the stored tokens alone.
                self.tokens.clear()
            message = extract_error_message(parsed if parsed is not None else text)
            raise error_for_status(
                response.status_code,
                message,
                body=parsed if parsed is not None else text,
                url=url,
                authenticated=authenticated,
            )

        return TransportResponse(
            status_code=response.status_code,
            json=parsed,
            text=text,
            # Lowercase header keys so lookups by the (always-lowercase) header
            # constants match regardless of the casing the server/Cloudflare used
            # on the wire — HTTP headers are case-insensitive, but a plain dict is not.
            headers={str(k).lower(): v for k, v in response.headers.items()},
            url=url,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def __aenter__(self) -> "AsyncTransport":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
