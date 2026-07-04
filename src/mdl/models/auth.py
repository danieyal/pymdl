"""Auth & profile models (spec §4 'Auth & profile')."""

from __future__ import annotations

from typing import Optional

from pydantic import field_validator

from .base import Images, MDLModel, resolve_image_url


class AuthResponse(MDLModel):
    access_token: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None


class ProfileResponse(MDLModel):
    """Own profile (``GET /users/settings``)."""

    email: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    location: Optional[str] = None
    ipcountry: Optional[str] = None
    gender: Optional[str] = None
    joined_at: Optional[str] = None
    email_verified: Optional[bool] = None
    vip: Optional[bool] = None
    about: Optional[str] = None
    images: Optional[Images] = None
    dob: Optional[str] = None
    dob_privacy: Optional[bool] = None
    hide_ads: Optional[bool] = None  # response-only; toJson omits it


class UserProfileResponse(MDLModel):
    """Person page (``GET /people/{id}``)."""

    id: Optional[int] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    family_name: Optional[str] = None
    original_name: Optional[str] = None
    biography: Optional[str] = None
    permalink: Optional[str] = None
    slug: Optional[str] = None
    birthday: Optional[str] = None
    dod: Optional[str] = None
    nationality: Optional[str] = None
    thumbnail: Optional[str] = None
    images: Optional[Images] = None
    flowers: Optional[int] = None
    ranked: Optional[int] = None
    likes: Optional[int] = None
    enable_ads: Optional[bool] = None
    liked: Optional[bool] = None

    @field_validator("thumbnail")
    @classmethod
    def _resolve_thumb(cls, v: Optional[str]) -> Optional[str]:
        return resolve_image_url(v)


class FriendRole(MDLModel):
    name: Optional[str] = None
    color: Optional[str] = None


class FriendStatus(MDLModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_friend: Optional[bool] = None
    request_sent: Optional[bool] = None
    request_pending: Optional[bool] = None
    is_blocking: Optional[bool] = None
    is_blocked: Optional[bool] = None
    is_following: Optional[bool] = None


class FriendProfile(MDLModel):
    """``GET /users/{id}``."""

    username: Optional[str] = None
    display_name: Optional[str] = None
    location: Optional[str] = None
    gender: Optional[str] = None
    joined_at: Optional[str] = None
    email_verified: Optional[bool] = None
    account_verified: Optional[bool] = None
    vip: Optional[bool] = None
    elite: Optional[bool] = None
    follows_list_privacy: Optional[int] = None
    profile_feeds_privacy: Optional[int] = None
    about: Optional[str] = None
    following: Optional[int] = None
    followers: Optional[int] = None
    points: Optional[int] = None
    contributions_points: Optional[int] = None
    contributions_level: Optional[int] = None
    images: Optional[Images] = None
    dob: Optional[str] = None
    status: Optional[FriendStatus] = None
    roles: Optional[list[FriendRole]] = None


class Urls(MDLModel):
    cover: Optional[str] = None
    full: Optional[str] = None
    medium: Optional[str] = None
    thumbnail: Optional[str] = None


class ProfileUploadResponse(MDLModel):
    """Result of a multipart upload (``POST /upload/bearer``)."""

    title: Optional[str] = None
    filename: Optional[str] = None
    domain: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    link: Optional[str] = None
    url: Optional[str] = None
    urls: Optional[Urls] = None


class ActionResult(MDLModel):
    code: Optional[int] = None
    message: Optional[str] = None
