"""Coins, subscription, flowers, gamification, calendar & misc models (spec §4)."""

from __future__ import annotations

import datetime as _dt
from typing import Any, Optional

from .base import MDLModel


class Coin(MDLModel):
    id: Optional[Any] = None
    name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    order_id: Optional[int] = None
    price_id: Optional[int] = None
    amount: Optional[int] = None
    coins: Optional[int] = None
    percentage: Optional[int] = None
    iap_pid: Optional[str] = None


class CoinResponse(MDLModel):
    items: Optional[list[Coin]] = None
    balance: Optional[int] = None


class Activity(MDLModel):
    id: Optional[Any] = None
    name: Optional[str] = None
    description: Optional[str] = None
    balance: Optional[int] = None
    tier: Optional[Any] = None


class ActivitiesResponse(MDLModel):
    balance: Optional[int] = None
    activities: Optional[list[Activity]] = None


class Subscription(MDLModel):
    id: Optional[int] = None
    product_id: Optional[int] = None
    email: Optional[str] = None
    sub_id: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    method_data: Optional[Any] = None
    amount: Optional[int] = None
    quantity: Optional[int] = None
    status: Optional[bool] = None
    live_mode: Optional[bool] = None
    paid: Optional[bool] = None
    active: Optional[bool] = None
    period_interval: Optional[str] = None
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    period_cycle: Optional[int] = None
    canceled: Optional[bool] = None
    canceled_at: Optional[int] = None
    ended_at: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SubscriptionHistory(MDLModel):
    id: Optional[Any] = None
    amount: Optional[int] = None
    quantity: Optional[int] = None
    method: Optional[str] = None
    attempted: Optional[bool] = None
    paid: Optional[bool] = None
    refunded: Optional[bool] = None
    discount: Optional[int] = None
    created_at: Optional[str] = None


class SubscriptionSettings(MDLModel):
    vip_status: Optional[bool] = None
    vip_badge: Optional[bool] = None
    hide_ads: Optional[bool] = None


class MySubscription(MDLModel):
    history: Optional[list[SubscriptionHistory]] = None
    settings: Optional[SubscriptionSettings] = None
    subscription: Optional[Subscription] = None


class PersonGiftProcess(MDLModel):
    balance: Optional[int] = None
    max_power: Optional[int] = None
    sent: Optional[int] = None
    price: Optional[int] = None
    prices: Optional[list[int]] = None


class Entries(MDLModel):
    """Leaderboard entry."""

    id: Optional[int] = None
    url: Optional[str] = None
    display_name: Optional[str] = None
    nationality: Optional[str] = None
    image_url: Optional[str] = None
    total_flowers: Optional[int] = None
    ranked: Optional[int] = None
    previous_rank: Optional[int] = None
    current_rank: Optional[int] = None


class Leaderboard(MDLModel):
    time_period: Optional[Any] = None
    entries: Optional[list[Entries]] = None


def _from_timestamp(value: Optional[int]) -> Optional[_dt.datetime]:
    return _dt.datetime.fromtimestamp(value, _dt.timezone.utc) if value else None


class EpisodeItem(MDLModel):
    """One airing in the calendar (``POST /calendar/episodes``).

    ``rid`` is the title id (it matches an :class:`EpisodeRelationship`'s ``id``);
    ``episode_number`` is ``0`` for a movie or special. Timestamps are Unix seconds.
    """

    id: Optional[Any] = None
    rid: Optional[Any] = None
    episode_number: Optional[int] = None
    released_at: Optional[int] = None
    #: Minutes; ``0`` when unknown.
    duration: Optional[int] = None
    permalink: Optional[str] = None
    #: Set when the airing was rescheduled; the originally announced time.
    original_release_date: Optional[int] = None

    @property
    def released_datetime(self) -> Optional[_dt.datetime]:
        """:attr:`released_at` as an aware UTC datetime."""
        return _from_timestamp(self.released_at)

    @property
    def original_release_datetime(self) -> Optional[_dt.datetime]:
        return _from_timestamp(self.original_release_date)


class EpisodeRelationship(MDLModel):
    id: Optional[Any] = None
    title: Optional[str] = None
    ranking: Optional[int] = None
    popularity: Optional[int] = None
    country: Optional[str] = None
    content_type: Optional[str] = None
    type: Optional[str] = None
    synopsis: Optional[str] = None
    url: Optional[str] = None
    #: Comma-separated genre names, e.g. ``"Life,Drama"``.
    genres: Optional[Any] = None
    thumbnail: Optional[str] = None
    cover: Optional[str] = None
    rating: Optional[float] = None
    timezone: Optional[str] = None
    #: ``True`` when the title is on one of the logged-in user's lists.
    add_status: Optional[Any] = None


class Episodes(MDLModel):
    """The airing calendar: a rolling week of episodes, starting the previous UTC day.

    ``items`` are the airings and ``relationships`` the titles they belong to; see
    :meth:`title_for`.
    """

    items: Optional[list[EpisodeItem]] = None
    relationships: Optional[list[EpisodeRelationship]] = None

    def title_for(self, item: EpisodeItem) -> Optional[EpisodeRelationship]:
        """The relationship (title) an airing belongs to."""
        for rel in self.relationships or []:
            if rel.id == item.rid:
                return rel
        return None


class Quarter(MDLModel):
    id: Optional[int] = None
    title: Optional[str] = None
    episodes: Optional[int] = None
    ranking: Optional[int] = None
    popularity: Optional[int] = None
    country: Optional[str] = None
    content_type: Optional[str] = None
    type: Optional[str] = None
    synopsis: Optional[str] = None
    released_at: Optional[str] = None
    url: Optional[str] = None
    genres: Optional[Any] = None
    thumbnail: Optional[str] = None
    cover: Optional[str] = None
    rating: Optional[float] = None
    timezone: Optional[str] = None
    add_status: Optional[bool] = None


class PersonStats(MDLModel):
    comments: Optional[int] = None
    feeds: Optional[int] = None
    reviews: Optional[int] = None
    episode_reviews: Optional[int] = None
    custom_lists: Optional[int] = None
    friends: Optional[int] = None
    recommendations: Optional[int] = None


class PersonSummary(MDLModel):
    """Per-content-type totals, e.g. ``{"type": "Drama", "watched": 3343, ...}``.

    ``watched`` counts episodes (one per movie), ``minutes`` the time spent on them.
    """

    type: Optional[str] = None
    collected: Optional[int] = None
    watched: Optional[int] = None
    minutes: Optional[int] = None
    ratings: Optional[int] = None


class RatingsSummary(MDLModel):
    total: Optional[int] = None
    #: Score (as a string such as ``"8.5"``) to the number of titles given that score.
    distribution: Optional[dict[str, int]] = None

    @property
    def mean(self) -> Optional[float]:
        """The average score across rated titles, or ``None`` with no ratings."""
        pairs = [(float(score), count) for score, count in (self.distribution or {}).items()]
        total = sum(count for _, count in pairs)
        if not total:
            return None
        return sum(score * count for score, count in pairs) / total


class UserStats(PersonStats):
    """``GET /users/{id}/stats`` — list totals, watch time and rating distribution.

    ``mylists`` maps a list segment (``watchlist``, ``completed``, ``plantowatch``,
    ``onhold``, ``dropped``, ``notinterested``) to per-type totals. ``stats`` holds the
    overall totals, split into ``"Shows"`` and ``"Movie"``.
    """

    mylists: Optional[dict[str, list[PersonSummary]]] = None
    stats: Optional[list[PersonSummary]] = None
    ratings: Optional[RatingsSummary] = None

    def total(self, type: Optional[str] = None) -> PersonSummary:
        """Sum :attr:`stats` across types, or for one ``type`` (``"Shows"``/``"Movie"``)."""
        rows = [row for row in self.stats or [] if type is None or row.type == type]
        return PersonSummary(
            type=type,
            collected=sum(row.collected or 0 for row in rows),
            watched=sum(row.watched or 0 for row in rows),
            minutes=sum(row.minutes or 0 for row in rows),
            ratings=sum(row.ratings or 0 for row in rows),
        )


class AwardResponse(MDLModel):
    awards: Optional[list[Any]] = None
