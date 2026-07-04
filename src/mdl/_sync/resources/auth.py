"""Auth, account and people/users resources (UserRepository, spec §3)."""

from __future__ import annotations

from typing import Any, Optional

from ..._request import PreparedRequest
from ...auth import generate_device_id, md5_password
from ...config import UPLOAD_URL
from ...models.auth import (
    ActionResult,
    AuthResponse,
    FriendProfile,
    ProfileResponse,
    ProfileUploadResponse,
    UserProfileResponse,
)
from ...models.misc import ActivitiesResponse, Coin, CoinResponse, PersonStats
from ...models.reviews import CreditsResponse
from ...models.titles import Movie
from .base import Resource


class AuthResource(Resource):
    """Login, social auth, registration and password reset."""

    def _device_id(self, device_id: Optional[str]) -> str:
        return device_id or self._transport.config.device_id or generate_device_id()

    def _store(self, auth: AuthResponse) -> AuthResponse:
        self._transport.tokens.set_token(auth.access_token)
        if auth.refresh_token:
            self._transport.tokens.set_refresh_token(auth.refresh_token)
        return auth

    def login(
        self, username: str, password: str, *, device_id: Optional[str] = None
    ) -> AuthResponse:
        """``POST /auth/login`` — password is MD5-hashed before sending."""
        req = PreparedRequest(
            "POST",
            "/auth/login",
            params={"device_id": self._device_id(device_id)},
            json={"username": username, "password": md5_password(password)},
            auth=False,
        )
        return self._store(self._model(self._transport.request(req), AuthResponse))

    def login_social(self, token: str, *, device_id: Optional[str] = None) -> AuthResponse:
        """``POST /auth/oauth2/firebase`` with a Firebase token."""
        req = PreparedRequest(
            "POST",
            "/auth/oauth2/firebase",
            params={"device_id": self._device_id(device_id)},
            json={"token": token},
            auth=False,
        )
        return self._store(self._model(self._transport.request(req), AuthResponse))

    def create_social_user(
        self, token: str, username: str, display_name: str, email: str
    ) -> AuthResponse:
        """``POST /auth/oauth2/firebase?create=true`` — register via a social token."""
        req = PreparedRequest(
            "POST",
            "/auth/oauth2/firebase",
            params={"create": "true"},
            json={
                "token": token,
                "username": username,
                "display_name": display_name,
                "password": "",
                "email": email,
            },
            auth=False,
        )
        return self._store(self._model(self._transport.request(req), AuthResponse))

    def register(self, username: str, email: str, password: str) -> AuthResponse:
        """``POST /users`` — returns a SuccessBlock wrapping an :class:`AuthResponse`."""
        req = PreparedRequest(
            "POST",
            "/users",
            json={"password": md5_password(password), "username": username, "email": email},
        )
        resp = self._transport.request(req)
        data = resp.json.get("data") if isinstance(resp.json, dict) else resp.json
        return self._store(AuthResponse.model_validate(data))

    def reset_password(self, email: str) -> Optional[ActionResult]:
        req = PreparedRequest("POST", "/auth/reset_password", json={"email": email})
        return self._model_opt(self._transport.request(req), ActionResult)

    def logout(self) -> None:
        """Clear locally-stored bearer/refresh tokens."""
        self._transport.tokens.clear()


class AccountResource(Resource):
    """Current-user settings, verification, devices, payments (UserRepository)."""

    def get_profile(self) -> ProfileResponse:
        req = PreparedRequest("GET", "/users/settings")
        return self._model(self._transport.request(req), ProfileResponse)

    def update_profile_info(
        self,
        *,
        display_name: Optional[str] = None,
        location: Optional[str] = None,
        gender: Optional[str] = None,
        dob: Optional[str] = None,
        dob_privacy: Optional[bool] = None,
    ) -> str:
        req = PreparedRequest(
            "PATCH",
            "/users/settings",
            params={"setting": "account"},
            json={
                "display_name": display_name,
                "location": location,
                "gender": gender,
                "dob": dob,
                "dob_privacy": dob_privacy,
            },
        )
        return self._str(self._transport.request(req))

    def update_email(self, email: str, password: str) -> ProfileResponse:
        req = PreparedRequest(
            "PATCH",
            "/users/settings",
            params={"setting": "email"},
            json={"email": email, "password": md5_password(password)},
        )
        return self._model(self._transport.request(req), ProfileResponse)

    def get_privacy(self) -> int:
        """``GET /users/settings/privacy`` → ``profile.read.feeds`` (``-2`` on failure)."""
        req = PreparedRequest("GET", "/users/settings/privacy")
        resp = self._transport.request(req)
        data = resp.json
        try:
            return int(data["profile"]["read"]["feeds"])
        except (KeyError, TypeError, ValueError):
            return -2

    def update_privacy(self, profile_feed: int) -> bool:
        req = PreparedRequest(
            "PATCH", "/users/settings/privacy", json={"profile_feed": profile_feed}
        )
        return self._bool(self._transport.request(req))

    def change_password(
        self, password: str, new_password: str, confirm_password: str
    ) -> str:
        """``POST /users/change_password`` — plaintext (not hashed), per spec."""
        req = PreparedRequest(
            "POST",
            "/users/change_password",
            json={
                "password": password,
                "new_password": new_password,
                "confirm_password": confirm_password,
            },
        )
        return self._str(self._transport.request(req))

    def deactivate(self, password: str, reason: str) -> bool:
        """``POST /users/deactivate`` — plaintext password, per spec."""
        req = PreparedRequest(
            "POST", "/users/deactivate", json={"password": password, "reason": reason}
        )
        return self._bool(self._transport.request(req))

    def verify_email(self, code: str) -> bool:
        req = PreparedRequest("POST", "/users/verify_email", params={"code": code})
        return self._bool(self._transport.request(req))

    def resend_verification(self) -> bool:
        req = PreparedRequest("POST", "/users/resend_verify_email")
        return self._bool(self._transport.request(req))

    def active_user(self, device_id: Optional[str] = None) -> bool:
        did = device_id or self._transport.config.device_id or ""
        req = PreparedRequest("GET", "/users/logged", params={"device_id": did})
        return self._bool(self._transport.request(req))

    def send_device_token(
        self, device_id: str, token: str, *, device_os: str = "android"
    ) -> bool:
        req = PreparedRequest(
            "POST",
            "/users/device_token",
            json={"device_id": device_id, "device_os": device_os, "token": token},
        )
        return self._bool(self._transport.request(req))

    def delete_device_token(self, device_id: str) -> bool:
        req = PreparedRequest(
            "DELETE", "/users/device_token", json={"device_id": device_id}
        )
        return self._bool(self._transport.request(req))

    def map_profile_picture(self, picture: str) -> bool:
        req = PreparedRequest("PATCH", "/users/picture", json={"picture": picture})
        return self._bool(self._transport.request(req))

    def upload_profile_image(
        self, content: bytes, *, filename: str = "upload.jpg"
    ) -> Optional[ProfileUploadResponse]:
        """``POST /upload/bearer`` (multipart) with ``category=users``."""
        req = PreparedRequest(
            "POST",
            UPLOAD_URL,
            multipart=True,
            data={"category": "users"},
            files={"file": (filename, content)},
        )
        return self._model_opt(self._transport.request(req), ProfileUploadResponse)

    def get_activities(self) -> ActivitiesResponse:
        req = PreparedRequest("GET", "/users/activities")
        return self._model(self._transport.request(req), ActivitiesResponse)

    def claim_reward(self, activity_id: Any, tier: Any) -> bool:
        req = PreparedRequest(
            "POST", f"/users/activities/{activity_id}/claim", params={"tier": tier}
        )
        return self._bool(self._transport.request(req))

    def get_coins(self) -> Optional[CoinResponse]:
        req = PreparedRequest("GET", "/payment/coins")
        return self._model_opt(self._transport.request(req), CoinResponse)

    def get_plans(self) -> list[Coin]:
        req = PreparedRequest("GET", "/payment/plans")
        return self._list(self._transport.request(req), Coin)

    def verify_purchase(
        self, payload: Any, *, type: str, store: str = "playstore"
    ) -> bool:
        req = PreparedRequest(
            "POST", "/iap/verify", params={"store": store, "type": type}, json=payload
        )
        return self._bool(self._transport.request(req))


class UsersResource(Resource):
    """Other users and people pages."""

    def get_user_info(self, user_id: Any) -> Optional[FriendProfile]:
        req = PreparedRequest("GET", f"/users/{user_id}")
        return self._model_opt(self._transport.request(req), FriendProfile)

    def get_person(self, person_id: Any) -> UserProfileResponse:
        req = PreparedRequest("GET", f"/people/{person_id}")
        return self._model(self._transport.request(req), UserProfileResponse)

    def get_person_credits(self, person_id: Any) -> CreditsResponse:
        req = PreparedRequest("GET", f"/people/{person_id}/credits")
        return self._model(self._transport.request(req), CreditsResponse)

    def like_person(self, person_id: Any, liked: bool = True) -> str:
        req = PreparedRequest(
            "POST", f"/people/{person_id}/likes", json={"liked": liked}
        )
        return self._str(self._transport.request(req))

    def get_user_stats(self, user_id: Any) -> PersonStats:
        req = PreparedRequest("GET", f"/users/{user_id}/stats")
        return self._model(self._transport.request(req), PersonStats)

    def get_user_watchlist(self, **params: Any) -> list[Movie]:
        req = PreparedRequest("GET", "/sync/mylist/watchlist", params=params or None)
        return self._list(self._transport.request(req), Movie)
