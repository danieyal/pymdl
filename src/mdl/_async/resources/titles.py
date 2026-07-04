"""Titles, search, explore, reviews and comments resources (spec §3)."""

from __future__ import annotations

from typing import Any, Optional

from ..._request import PreparedRequest
from ...models.auth import UserProfileResponse
from ...models.base import SearchEntry
from ...models.reviews import (
    Comment,
    CommentReplyResponse,
    CommentResponse,
    CreditsResponse,
    ReviewResponse,
)
from ...models.titles import Movie, MovieTitle, TitleResponse
from .base import AsyncResource


class TitlesResource(AsyncResource):
    """TitleRepository — title detail, progress, reviews, recs, credits, genres, tags."""

    async def get_title(self, title_id: Any) -> TitleResponse:
        req = PreparedRequest(
            "GET", f"/titles/{title_id}", params={"expand": 1}, auth=False
        )
        return self._model(await self._transport.request(req), TitleResponse)

    async def get_progress(self, title_id: Any) -> Optional[Movie]:
        req = PreparedRequest("GET", f"/titles/{title_id}/progress")
        return self._model_opt(await self._transport.request(req), Movie)

    async def get_comment_count(self, title_id: Any) -> int:
        """Total comment count, read from the ``x-pagination-total`` header."""
        req = PreparedRequest("GET", f"/titles/{title_id}/comments")
        return self._page(await self._transport.request(req), Comment, page=1).total or 0

    async def get_reviews(self, title_id: Any) -> list[ReviewResponse]:
        req = PreparedRequest("GET", f"/titles/{title_id}/reviews")
        return self._list(await self._transport.request(req), ReviewResponse)

    async def get_reviews_page(
        self, title_id: Any, *, sort: str = "helpful", page: int = 1, limit: int = 20
    ) -> list[ReviewResponse]:
        req = PreparedRequest(
            "GET",
            f"/titles/{title_id}/reviews",
            params={"sort": sort, "expand": 1, "page": page, "limit": limit},
        )
        return self._list(await self._transport.request(req), ReviewResponse)

    async def get_recommendations(self, title_id: Any) -> list[MovieTitle]:
        req = PreparedRequest(
            "GET", f"/titles/{title_id}/recommendations", auth=False
        )
        return self._list(await self._transport.request(req), MovieTitle)

    async def get_credits(self, title_id: Any) -> CreditsResponse:
        req = PreparedRequest("GET", f"/titles/{title_id}/credits", auth=False)
        return self._model(await self._transport.request(req), CreditsResponse)

    async def get_genres(self) -> list[SearchEntry]:
        req = PreparedRequest("GET", "/genres", auth=False)
        return self._list(await self._transport.request(req), SearchEntry)

    async def search_tags(self, query: str) -> list[SearchEntry]:
        req = PreparedRequest("GET", "/tags/search", params={"q": query}, auth=False)
        return self._list(await self._transport.request(req), SearchEntry)


class SearchResource(AsyncResource):
    """SearchRepository — POST-based title/person search."""

    async def titles(
        self,
        query: str,
        *,
        page: int = 1,
        edge: int = 1,
        synopsis: bool = False,
        **filters: Any,
    ) -> list[MovieTitle]:
        params: dict[str, Any] = {"edge": edge, "q": query, "page": page, **filters}
        if synopsis:
            params["synopsis"] = 1
        req = PreparedRequest("POST", "/search/titles", params=params)
        return self._list(await self._transport.request(req), MovieTitle)

    async def top_dramas(self) -> list[MovieTitle]:
        req = PreparedRequest(
            "POST",
            "/search/titles",
            params={"types": "68,77", "sort": "top", "page": 1, "edge": 1},
        )
        return self._list(await self._transport.request(req), MovieTitle)

    async def people(self, query: str = "", *, page: int = 1) -> list[UserProfileResponse]:
        if query:
            params: dict[str, Any] = {"q": query, "page": page}
        else:
            params = {"page": 1, "limit": 50, "sort": "popular"}
        req = PreparedRequest("POST", "/search/people", params=params)
        return self._list(await self._transport.request(req), UserProfileResponse)


class ExploreResource(AsyncResource):
    """MovieExploreRepository — path-based movie feeds (trending, top_airing, …)."""

    async def fetch(self, path: str, **params: Any) -> list[MovieTitle]:
        path = path.lstrip("/")
        req = PreparedRequest("GET", f"/{path}", params=params or None)
        return self._list(await self._transport.request(req), MovieTitle)

    async def trending(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/trending", **params)

    async def top_airing(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/top_airing", **params)

    async def upcoming(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/upcoming", **params)

    async def recommended(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/recommended", **params)

    async def currently_watching(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/currently_watching", **params)

    async def top_movies(self, **params: Any) -> list[MovieTitle]:
        return await self.fetch("titles/top_movies", **params)


class ReviewsResource(AsyncResource):
    """Review CRUD, voting, and detail (TitleRepository + ReviewRepository)."""

    async def submit(
        self,
        *,
        review: str,
        headline: str,
        completed: bool = False,
        dropped: bool = False,
        episodes_seen: int = 0,
        parent_id: int = 0,
        lang_iso: str = "en-US",
        story: float = 0.0,
        acting: float = 0.0,
        music: float = 0.0,
        rewatch: float = 0.0,
        overall: float = 0.0,
        spoiler: bool = False,
    ) -> str:
        body = {
            "completed": completed,
            "dropped": dropped,
            "episodes_seen": episodes_seen,
            "headline": headline,
            "parent_id": parent_id,
            "lang_iso": lang_iso,
            "ratings": {
                "story": story,
                "acting": acting,
                "music": music,
                "rewatch": rewatch,
                "overall": overall,
            },
            "review": review,
            "spoiler": spoiler,
        }
        req = PreparedRequest("POST", "/reviews", json=body)
        return self._str(await self._transport.request(req))

    async def edit(self, review_id: Any, **fields: Any) -> str:
        req = PreparedRequest("PATCH", f"/reviews/{review_id}", json=fields)
        return self._str(await self._transport.request(req))

    async def delete(self, review_id: Any) -> str:
        req = PreparedRequest("DELETE", f"/reviews/{review_id}")
        return self._str(await self._transport.request(req))

    async def vote(self, review_id: Any, direction: int) -> int:
        req = PreparedRequest(
            "POST", f"/reviews/{review_id}/vote", json={"dir": direction}
        )
        return self._int(await self._transport.request(req))

    async def check_already_wrote(self, title_id: Any) -> bool:
        req = PreparedRequest("GET", "/reviews/check", params={"title_id": title_id})
        return self._bool(await self._transport.request(req))

    async def get(self, review_id: Any) -> ReviewResponse:
        req = PreparedRequest("GET", f"/reviews/{review_id}")
        return self._model(await self._transport.request(req), ReviewResponse)


class CommentsResource(AsyncResource):
    """Comment listing and CRUD across content types (CommentManager + repos)."""

    async def list(
        self, ptype: str, pid: Any, *, page: int = 1, **params: Any
    ) -> CommentResponse:
        req = PreparedRequest(
            "GET", "/comments", params={"ptype": ptype, "pid": pid, "page": page, **params}
        )
        return self._model(await self._transport.request(req), CommentResponse)

    async def post(
        self,
        *,
        pid: Any,
        ptype: str,
        message: str,
        reply_to: Optional[int] = None,
        spoiler: Optional[int] = None,
    ) -> CommentReplyResponse:
        body: dict[str, Any] = {"pid": pid, "ptype": ptype, "message": message}
        if reply_to is not None:
            body["reply_to"] = reply_to
        if spoiler is not None:
            body["spoiler"] = spoiler
        req = PreparedRequest("POST", "/comments", json=body)
        return self._model(await self._transport.request(req), CommentReplyResponse)

    async def update(
        self, comment_id: Any, *, message: str, spoiler: Optional[int] = None
    ) -> Optional[Comment]:
        req = PreparedRequest(
            "PATCH", f"/comments/{comment_id}", json={"message": message, "spoiler": spoiler}
        )
        return self._model_opt(await self._transport.request(req), Comment)

    async def delete(self, comment_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/comments/{comment_id}")
        return self._bool(await self._transport.request(req))

    async def like(self, comment_id: Any, liked: bool = True) -> bool:
        req = PreparedRequest(
            "POST", f"/comments/{comment_id}/likes", json={"liked": liked}
        )
        return self._bool(await self._transport.request(req))
