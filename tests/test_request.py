"""Unit tests for the pure request-building layer (no network)."""

from __future__ import annotations

from mdl._request import (
    PreparedRequest,
    build_headers,
    clean_params,
    extract_error_message,
)
from mdl.auth import md5_password
from mdl.config import ClientConfig, Environment


def _config(**kw) -> ClientConfig:
    return ClientConfig(api_key="k", app_version="9.9", **kw)


def test_md5_password_matches_known_vector() -> None:
    # md5("password") is a well-known digest.
    assert md5_password("password") == "5f4dcc3b5aa765d61d8327deb882cf99"


def test_headers_always_include_key_and_version() -> None:
    headers = build_headers(_config(), token=None)
    assert headers["mdl-api-key"] == "k"
    assert headers["version"] == "9.9"
    assert headers["Content-Type"] == "application/json"
    assert "Authorization" not in headers


def test_headers_attach_bearer_when_token_and_auth() -> None:
    headers = build_headers(_config(), token="abc", auth=True)
    assert headers["Authorization"] == "Bearer abc"


def test_headers_omit_bearer_when_auth_false() -> None:
    headers = build_headers(_config(), token="abc", auth=False)
    assert "Authorization" not in headers


def test_multipart_strips_content_type() -> None:
    headers = build_headers(_config(), token=None, multipart=True)
    assert "Content-Type" not in headers


def test_accept_language_sent_when_configured() -> None:
    headers = build_headers(_config(lang_code="ko-KR"), token=None)
    assert headers["Accept-Language"] == "ko-KR"


def test_clean_params_drops_none_and_coerces_bools() -> None:
    assert clean_params({"a": None, "b": True, "c": False, "d": 3}) == {
        "b": 1,
        "c": 0,
        "d": 3,
    }
    assert clean_params(None) is None
    assert clean_params({"a": None}) is None


def test_extract_error_message_prefers_message_then_error() -> None:
    assert extract_error_message({"message": "boom"}) == "boom"
    assert extract_error_message({"error": "bad"}) == "bad"
    assert extract_error_message("raw text") == "raw text"
    assert extract_error_message({}) == "request failed"


def test_prepared_request_url_relative_and_absolute() -> None:
    base = Environment.PRODUCTION.base_url
    rel = PreparedRequest("GET", "/titles/1")
    assert rel.url(base) == f"{base}/titles/1"
    absolute = PreparedRequest("POST", "https://app-api.mydramalist.com/upload/bearer")
    assert absolute.url(base) == "https://app-api.mydramalist.com/upload/bearer"
