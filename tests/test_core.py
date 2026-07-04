"""Core plumbing: config resolution, token stores, pagination, models, client wiring."""

from __future__ import annotations

import json

import pytest

from mdl import (
    ClientConfig,
    Environment,
    FileTokenStore,
    InMemoryTokenStore,
    MDLClient,
    Page,
)
from mdl.models import (
    Images,
    MovieStatusType,
    MovieTitle,
    TitleResponse,
    UserProfileResponse,
)
from mdl.models.base import resolve_image_url

# --- config --------------------------------------------------------------

def test_config_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("MDL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="mdl-api-key"):
        ClientConfig.resolve(None)


def test_config_reads_env(monkeypatch) -> None:
    monkeypatch.setenv("MDL_API_KEY", "env-key")
    monkeypatch.setenv("MDL_APP_VERSION", "1.2.3")
    config = ClientConfig.resolve(None)
    assert config.api_key == "env-key"
    assert config.app_version == "1.2.3"


def test_environment_base_urls() -> None:
    assert Environment.PRODUCTION.base_url == "https://app-api.mydramalist.com/v1"
    assert Environment.STAGING.base_url == "https://stagingv6api.mydramalist.com/v1"


def test_client_uses_staging_base_url() -> None:
    client = MDLClient(api_key="k", environment=Environment.STAGING)
    assert client.config.base_url == "https://stagingv6api.mydramalist.com/v1"
    client.close()


# --- token stores --------------------------------------------------------

def test_in_memory_token_store_roundtrip() -> None:
    store = InMemoryTokenStore()
    assert store.get_token() is None
    store.set_token("abc")
    store.set_refresh_token("ref")
    assert store.get_token() == "abc"
    assert store.get_refresh_token() == "ref"
    store.clear()
    assert store.get_token() is None
    assert store.get_refresh_token() is None


def test_file_token_store_persists(tmp_path) -> None:
    path = tmp_path / "token.json"
    store = FileTokenStore(path)
    store.set_token("tok")
    store.set_refresh_token("ref")
    # a fresh instance reads the same file
    reopened = FileTokenStore(path)
    assert reopened.get_token() == "tok"
    assert reopened.get_refresh_token() == "ref"
    assert json.loads(path.read_text("utf-8"))["token"] == "tok"


def test_file_token_store_missing_file_is_empty(tmp_path) -> None:
    store = FileTokenStore(tmp_path / "does-not-exist.json")
    assert store.get_token() is None


def test_client_accepts_initial_token_and_custom_store() -> None:
    store = InMemoryTokenStore()
    client = MDLClient(api_key="k", token="seed", token_store=store)
    assert store.get_token() == "seed"
    assert client.tokens is store
    client.close()


# --- pagination ----------------------------------------------------------

def test_page_iteration_and_helpers() -> None:
    page = Page(items=[1, 2, 3], page=1, total=10)
    assert list(page) == [1, 2, 3]
    assert len(page) == 3
    assert not page.is_empty
    assert Page(items=[], page=2).is_empty


# --- models --------------------------------------------------------------

def test_resolve_image_url_variants() -> None:
    assert resolve_image_url(None) is None
    assert resolve_image_url("") == ""
    assert resolve_image_url("a/b.jpg") == "https://i.mydramalist.com/a/b.jpg"
    assert resolve_image_url("/a/b.jpg") == "https://i.mydramalist.com/a/b.jpg"
    assert resolve_image_url("//cdn/x.jpg") == "https://cdn/x.jpg"
    assert resolve_image_url("https://x/y.jpg") == "https://x/y.jpg"


def test_models_ignore_unknown_fields() -> None:
    title = TitleResponse.model_validate(
        {"id": 1, "title": "T", "some_new_field": "surprise", "another": 42}
    )
    assert title.id == 1
    assert not hasattr(title, "some_new_field")


def test_movie_title_watch_status_flatten_and_alias() -> None:
    movie = MovieTitle.model_validate(
        {"id": 3, "watch_status": {"status": 2}, "released_date": "2021-01-01"}
    )
    assert movie.watch_status == 2
    dumped = movie.model_dump(by_alias=True, exclude_none=True)
    assert dumped["release_date"] == "2021-01-01"
    assert "released_date" not in dumped


def test_movie_title_watch_status_accepts_scalar() -> None:
    assert MovieTitle.model_validate({"id": 3, "watch_status": 4}).watch_status == 4
    assert MovieTitle.model_validate({"id": 3, "watch_status": None}).watch_status is None


def test_images_model() -> None:
    images = Images.model_validate({"thumb": "t", "medium": "m", "poster": "p"})
    assert (images.thumb, images.medium, images.poster) == ("t", "m", "p")


def test_user_profile_thumbnail_resolution() -> None:
    person = UserProfileResponse.model_validate({"id": 1, "thumbnail": "p/1.jpg"})
    assert person.thumbnail == "https://i.mydramalist.com/p/1.jpg"


def test_movie_status_type_paths_and_labels() -> None:
    assert MovieStatusType.COMPLETED.mylist_path() == "/sync/mylist/completed"
    assert MovieStatusType.WATCHING.watchlist_path() == "/watchlist/watching"
    assert MovieStatusType.PLAN_TO_WATCH.label == "Plan to watch"


# --- client wiring -------------------------------------------------------

def test_all_resource_groups_present() -> None:
    client = MDLClient(api_key="k")
    for group in (
        "auth", "account", "users", "titles", "search", "explore", "reviews",
        "comments", "watchlist", "custom_lists", "feeds", "articles", "friends",
        "messages", "notifications", "groups", "subscription", "flowers", "awards",
        "reports", "calendar", "leaderboard",
    ):
        assert hasattr(client, group), f"missing resource group: {group}"
    client.close()
