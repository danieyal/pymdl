"""Coins, subscription, flowers, gamification, calendar & misc models (spec §4)."""

from __future__ import annotations

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


class EpisodeItem(MDLModel):
    id: Optional[Any] = None
    rid: Optional[Any] = None
    episode_number: Optional[int] = None
    released_at: Optional[str] = None
    duration: Optional[int] = None
    permalink: Optional[str] = None
    original_release_date: Optional[str] = None


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
    genres: Optional[Any] = None
    thumbnail: Optional[str] = None
    cover: Optional[str] = None
    rating: Optional[float] = None
    timezone: Optional[str] = None
    add_status: Optional[Any] = None


class Episodes(MDLModel):
    items: Optional[list[EpisodeItem]] = None
    relationships: Optional[list[EpisodeRelationship]] = None


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
    type: Optional[str] = None
    collected: Optional[int] = None
    watched: Optional[int] = None
    minutes: Optional[int] = None


class AwardResponse(MDLModel):
    awards: Optional[list[Any]] = None
