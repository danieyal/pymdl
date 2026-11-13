"""Titles, movies & watchlist models (spec §4 'Titles, movies & watchlist')."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional, Union

from pydantic import Field, field_validator

from .base import Images, MDLModel, SearchEntry, as_int_flag


class Trailer(MDLModel):
    id: Optional[int] = None


class MovieResourceResponse(MDLModel):
    xid: Optional[str] = None
    name: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None


class TitleResponse(MDLModel):
    """Full title detail (``GET /titles/{id}?expand=1``)."""

    id: int
    slug: Optional[str] = None
    title: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    episodes: Optional[int] = None
    rating: Optional[float] = None
    permalink: Optional[str] = None
    synopsis: Optional[str] = None
    type: Optional[str] = None
    language: Optional[str] = None
    images: Optional[Images] = None
    country: Optional[str] = None
    media_type: Optional[str] = None
    votes: Optional[int] = None
    aired_start: Optional[str] = None
    aired_end: Optional[str] = None
    released: Optional[str] = None  # response-only
    trailer: Optional[Trailer] = None
    watchers: Optional[int] = None
    ranked: Optional[int] = None
    popularity: Optional[int] = None
    runtime: Optional[int] = None
    reviews_count: Optional[int] = None
    recs_count: Optional[int] = None
    comments_count: Optional[int] = None
    certification: Optional[str] = None
    status: Optional[str] = None
    updated_at: Optional[int] = None
    release_dates_fmt: Optional[str] = None  # response-only
    enable_ads: Optional[bool] = None  # response-only
    alt_titles: Optional[list[SearchEntry]] = None
    genres: Optional[list[SearchEntry]] = None
    tags: Optional[list[SearchEntry]] = None
    sources: Optional[list[MovieResourceResponse]] = None

    @field_validator("alt_titles", mode="before")
    @classmethod
    def _wrap_alt_title_strings(cls, v: Any) -> Any:
        # The API now sends alt titles as plain strings; keep the ``{id, name}`` shape.
        if isinstance(v, list):
            return [{"name": item} if isinstance(item, str) else item for item in v]
        return v


class WatchStatusWrapper(MDLModel):
    status: Optional[int] = None


class MovieTitle(MDLModel):
    """Compact title (search / lists / recommendations)."""

    id: int
    title: Optional[str] = None
    synopsis: Optional[str] = None
    original_title: Optional[str] = None
    year: Optional[int] = None
    episodes: Optional[int] = None
    rating: Optional[float] = None
    aired_start: Optional[str] = None
    aired_end: Optional[str] = None
    # A bool in sync payloads; search results send the release date string instead.
    released: Optional[Union[bool, str]] = None
    type: Optional[str] = None
    media_type: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    images: Optional[Images] = None
    watch_status: Optional[int] = None
    rank: Optional[int] = None
    ended: Optional[bool] = None
    # response key is ``released_date``; request serialization uses ``release_date``.
    released_date: Optional[str] = Field(default=None, serialization_alias="release_date")
    category: Optional[str] = None
    #: Site path such as ``/18452-goblin`` (explore feeds, recommendations).
    permalink: Optional[str] = None
    can_add_item: Optional[bool] = None

    @field_validator("watch_status", mode="before")
    @classmethod
    def _flatten_watch_status(cls, v: Any) -> Optional[int]:
        return as_int_flag(v)


class WatchPoints(MDLModel):
    production: Optional[bool] = None
    story: Optional[bool] = None
    acting: Optional[bool] = None
    visual: Optional[bool] = None
    ost: Optional[bool] = None


class Movie(MDLModel):
    """A watchlist entry: a compact title plus the user's progress.

    ``list_id`` is the numeric watch status (see :attr:`MovieStatusType.list_id`); ``0``
    means the title is on none of the user's lists. Unset dates come back as
    ``"0000-00-00"`` (or ``"1970-01-01"`` for a start date), not ``null``.
    """

    #: The user's list-entry id (sync payloads only), not the title id.
    id: Optional[int] = None
    list_id: Optional[int] = None
    episode_seen: Optional[int] = None
    rating: Optional[float] = None
    priority: Optional[int] = None
    times_rewatched: Optional[int] = None
    rewatch_value: Optional[int] = None
    date_start: Optional[str] = None
    date_finish: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[str] = None
    watch_points: Optional[WatchPoints] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None  # response-only
    title: Optional[MovieTitle] = None
    deleted: Optional[bool] = None  # response-only

    @property
    def status(self) -> Optional["MovieStatusType"]:
        """The watch status for :attr:`list_id`, or ``None`` when not on a list."""
        return MovieStatusType.from_list_id(self.list_id)


class MovieStatusType(str, Enum):
    """Local watch-status enum → watchlist path segment (spec 'MovieStatus')."""

    WATCHING = "watching"
    PLAN_TO_WATCH = "plantowatch"
    COMPLETED = "completed"
    ON_HOLD = "onhold"
    DROPPED = "dropped"
    UNDECIDED = "undecided"
    NOT_INTERESTED = "notinterested"

    @property
    def label(self) -> str:
        return {
            MovieStatusType.WATCHING: "Currently Watching",
            MovieStatusType.PLAN_TO_WATCH: "Plan to watch",
            MovieStatusType.COMPLETED: "Completed",
            MovieStatusType.ON_HOLD: "On hold",
            MovieStatusType.DROPPED: "Dropped",
            MovieStatusType.UNDECIDED: "Undecided",
            MovieStatusType.NOT_INTERESTED: "Not interested",
        }[self]

    @property
    def mylist_segment(self) -> str:
        """Path segment under ``/sync/mylist/``.

        The sync API serves Currently Watching at ``/sync/mylist/watchlist``;
        ``/sync/mylist/watching`` is a 404.
        """
        if self is MovieStatusType.WATCHING:
            return "watchlist"
        return str(self.value)

    def mylist_path(self) -> str:
        return f"/sync/mylist/{self.mylist_segment}"

    def watchlist_path(self) -> str:
        return f"/watchlist/{self.value}"

    @property
    def list_id(self) -> Optional[int]:
        """The numeric ``list_id`` the sync API uses for this status.

        ``None`` for :attr:`UNDECIDED`, whose id has not been observed.
        """
        return _STATUS_LIST_IDS.get(self)

    @classmethod
    def from_list_id(cls, list_id: Optional[int]) -> Optional["MovieStatusType"]:
        """Map a sync ``list_id`` back to a status; ``None`` for 0 or unknown ids."""
        for status, value in _STATUS_LIST_IDS.items():
            if value == list_id:
                return status
        return None


#: ``list_id`` values observed on ``/sync/mylist/{segment}`` entries.
_STATUS_LIST_IDS = {
    MovieStatusType.WATCHING: 1,
    MovieStatusType.COMPLETED: 2,
    MovieStatusType.PLAN_TO_WATCH: 3,
    MovieStatusType.ON_HOLD: 4,
    MovieStatusType.DROPPED: 5,
    MovieStatusType.NOT_INTERESTED: 6,
}


class LastActivity(MDLModel):
    """Sync timestamps (``GET /sync/last_activities``)."""

    all: Optional[str] = None
    watching_at: Optional[str] = None
    completed_at: Optional[str] = None
    onhold_at: Optional[str] = None
    plan_to_watch_at: Optional[str] = None
    dropped_at: Optional[str] = None
    not_interested_at: Optional[str] = None
    rated_at: Optional[str] = None
    undecided_at: Optional[str] = None


class _SyncSuccess(MDLModel):
    titles: Optional[int] = None


class _NotFoundEntry(MDLModel):
    id: Optional[int] = None
    title: Optional[str] = None


class _SyncNotFound(MDLModel):
    titles: Optional[list[_NotFoundEntry]] = None


_FAILURE_PREFIX = re.compile(r"^code=\d+,\s*message=")


class SyncFailure(MDLModel):
    """A title the sync endpoint rejected, e.g. ``"This show has not aired yet."``."""

    id: Optional[int] = None
    message: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _strip_code_prefix(cls, v: Optional[str]) -> Optional[str]:
        # The server wraps its own error: "code=400, message=Invalid watch status."
        return _FAILURE_PREFIX.sub("", v) if v else v


class _SyncFailed(MDLModel):
    titles: Optional[list[SyncFailure]] = None


class SyncWatchListResponse(MDLModel):
    """Result of ``POST`` / ``DELETE /sync/mylist``.

    The endpoint answers ``200`` even when it rejects titles: those land in
    :attr:`failed` with the server's reason, and unknown title ids in :attr:`not_found`.
    :attr:`failures` combines both.
    """

    success: Optional[_SyncSuccess] = None
    not_found: Optional[_SyncNotFound] = None
    failed: Optional[_SyncFailed] = None
    deleted: Optional[Any] = None

    @property
    def failures(self) -> list[SyncFailure]:
        """Every title that was not saved: rejected ones, then unknown ids."""
        failed = list(self.failed.titles or []) if self.failed else []
        missing = self.not_found.titles or [] if self.not_found else []
        return failed + [SyncFailure(id=entry.id, message="Title not found.") for entry in missing]
