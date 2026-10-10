"""Exception hierarchy.

The app treats any non-200 response as an error, reading ``message`` / ``error`` from
the JSON body (spec §2, ``AppNetworkException``). We mirror that in :class:`MDLNetworkError`
and specialize common status codes.
"""

from __future__ import annotations

from typing import Any, Optional


class MDLError(Exception):
    """Base class for all errors raised by this library."""


class MDLConfigError(MDLError):
    """Invalid or missing client configuration (e.g. no api key)."""


class MDLNetworkError(MDLError):
    """A non-2xx HTTP response.

    ``status_code`` is the HTTP status; ``message`` is extracted from the JSON body's
    ``message`` or ``error`` key when present. ``body`` retains the raw parsed payload
    (or text) for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        body: Any = None,
        url: Optional[str] = None,
    ) -> None:
        super().__init__(f"[{status_code}] {message}" + (f" ({url})" if url else ""))
        self.status_code = status_code
        self.message = message
        self.body = body
        self.url = url


class MDLAuthError(MDLNetworkError):
    """Authentication failed.

    Raised for a 401 (the client clears any stored bearer token before raising) and for
    credentials rejected by :meth:`~mdl._async.resources.auth.AuthResource.login`, which
    the API reports as a 400.
    """


class MDLLoginRequiredError(MDLAuthError):
    """The endpoint needs a logged-in client but the request carried no bearer token.

    The API answers these requests with a bare ``400 Bad Request`` rather than a 401.
    Call ``client.auth.login()`` (or pass ``token=``) first.
    """


class MDLForbiddenError(MDLNetworkError):
    """403 Forbidden."""


class MDLNotFoundError(MDLNetworkError):
    """404 Not Found."""


class MDLRateLimitedError(MDLNetworkError):
    """429 Too Many Requests."""


class MDLServerError(MDLNetworkError):
    """5xx server error."""


#: Message of the bare 400 the API returns when a login-only endpoint gets no bearer token.
#: Other 400s carry a specific message (e.g. "Invalid or missing parameters. ...").
_LOGIN_REQUIRED_MESSAGE = "Bad Request"


def error_for_status(
    status_code: int, message: str, *, body: Any, url: str, authenticated: bool = True
) -> MDLNetworkError:
    """Map an HTTP status code to the most specific network-error subclass.

    ``authenticated`` says whether the request carried a bearer token; an anonymous
    request rejected with the bare ``400 Bad Request`` maps to
    :class:`MDLLoginRequiredError`.
    """
    if status_code == 400 and not authenticated and message == _LOGIN_REQUIRED_MESSAGE:
        return MDLLoginRequiredError(
            "This endpoint requires a logged-in client; call client.auth.login() first",
            status_code=status_code,
            body=body,
            url=url,
        )
    cls: type[MDLNetworkError]
    if status_code == 401:
        cls = MDLAuthError
    elif status_code == 403:
        cls = MDLForbiddenError
    elif status_code == 404:
        cls = MDLNotFoundError
    elif status_code == 429:
        cls = MDLRateLimitedError
    elif status_code >= 500:
        cls = MDLServerError
    else:
        cls = MDLNetworkError
    return cls(message, status_code=status_code, body=body, url=url)
