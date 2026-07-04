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
from .base import Resource


class TitlesResource(Resource):
    """TitleRepository — title detail, progress, reviews, recs, credits, genres, tags."""

    def get_title(self, title_id: Any) -> TitleResponse:
        req = PreparedRequest(
            "GET", f"/titles/{title_id}", params={"expand": 1}, auth=False
        )
        return self._model(self._transport.request(req), TitleResponse)

    def get_progress(self, title_id: Any) -> Optional[Movie]:
        req = PreparedRequest("GET", f"/titles/{title_id}/progress")
        return self._model_opt(self._transport.request(req), Movie)

    def get_comment_count(self, title_id: Any) -> int:
        """Total comment count, read from the ``x-pagination-total`` header."""
        req = PreparedRequest("GET", f"/titles/{title_id}/comments")
        return self._page(self._transport.request(req), Comment, page=1).total or 0

    def get_reviews(self, title_id: Any) -> list[ReviewResponse]:
        req = PreparedRequest("GET", f"/titles/{title_id}/reviews")
        return self._list(self._transport.request(req), ReviewResponse)

    def get_reviews_page(
        self, title_id: Any, *, sort: str = "helpful", page: int = 1, limit: int = 20
    ) -> list[ReviewResponse]:
        req = PreparedRequest(
            "GET",
            f"/titles/{title_id}/reviews",
            params={"sort": sort, "expand": 1, "page": page, "limit": limit},
        )
        return self._list(self._transport.request(req), ReviewResponse)

    def get_recommendations(self, title_id: Any) -> list[MovieTitle]:
        req = PreparedRequest(
            "GET", f"/titles/{title_id}/recommendations", auth=False
        )
        return self._list(self._transport.request(req), MovieTitle)

    def get_credits(self, title_id: Any) -> CreditsResponse:
        req = PreparedRequest("GET", f"/titles/{title_id}/credits", auth=False)
        return self._model(self._transport.request(req), CreditsResponse)

    def get_genres(self) -> list[SearchEntry]:
        req = PreparedRequest("GET", "/genres", auth=False)
        return self._list(self._transport.request(req), SearchEntry)

    def search_tags(self, query: str) -> list[SearchEntry]:
        req = PreparedRequest("GET", "/tags/search", params={"q": query}, auth=False)
        return self._list(self._transport.request(req), SearchEntry)


class SearchResource(Resource):
    """SearchRepository — POST-based title/person search."""

    def titles(
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
        return self._list(self._transport.request(req), MovieTitle)

    def top_dramas(self) -> list[MovieTitle]:
        req = PreparedRequest(
            "POST",
            "/search/titles",
            params={"types": "68,77", "sort": "top", "page": 1, "edge": 1},
        )
        return self._list(self._transport.request(req), MovieTitle)

    def people(self, query: str = "", *, page: int = 1) -> list[UserProfileResponse]:
        if query:
            params: dict[str, Any] = {"q": query, "page": page}
        else:
            params = {"page": 1, "limit": 50, "sort": "popular"}
        req = PreparedRequest("POST", "/search/people", params=params)
        return self._list(self._transport.request(req), UserProfileResponse)


class ExploreResource(Resource):
    """MovieExploreRepository — path-based movie feeds (trending, top_airing, …)."""

    def fetch(self, path: str, **params: Any) -> list[MovieTitle]:
        path = path.lstrip("/")
        req = PreparedRequest("GET", f"/{path}", params=params or None)
        return self._list(self._transport.request(req), MovieTitle)

    def trending(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/trending", **params)

    def top_airing(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/top_airing", **params)

    def upcoming(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/upcoming", **params)

    def recommended(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/recommended", **params)

    def currently_watching(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/currently_watching", **params)

    def top_movies(self, **params: Any) -> list[MovieTitle]:
        return self.fetch("titles/top_movies", **params)


class ReviewsResource(Resource):
    """Review CRUD, voting, and detail (TitleRepository + ReviewRepository)."""

    def submit(
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
        return self._str(self._transport.request(req))

    def edit(self, review_id: Any, **fields: Any) -> str:
        req = PreparedRequest("PATCH", f"/reviews/{review_id}", json=fields)
        return self._str(self._transport.request(req))

    def delete(self, review_id: Any) -> str:
        req = PreparedRequest("DELETE", f"/reviews/{review_id}")
        return self._str(self._transport.request(req))

    def vote(self, review_id: Any, direction: int) -> int:
        req = PreparedRequest(
            "POST", f"/reviews/{review_id}/vote", json={"dir": direction}
        )
        return self._int(self._transport.request(req))

    def check_already_wrote(self, title_id: Any) -> bool:
        req = PreparedRequest("GET", "/reviews/check", params={"title_id": title_id})
        return self._bool(self._transport.request(req))

    def get(self, review_id: Any) -> ReviewResponse:
        req = PreparedRequest("GET", f"/reviews/{review_id}")
        return self._model(self._transport.request(req), ReviewResponse)


class CommentsResource(Resource):
    """Comment listing and CRUD across content types (CommentManager + repos)."""

    def list(
        self, ptype: str, pid: Any, *, page: int = 1, **params: Any
    ) -> CommentResponse:
        req = PreparedRequest(
            "GET", "/comments", params={"ptype": ptype, "pid": pid, "page": page, **params}
        )
        return self._model(self._transport.request(req), CommentResponse)

    def post(
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
        return self._model(self._transport.request(req), CommentReplyResponse)

    def update(
        self, comment_id: Any, *, message: str, spoiler: Optional[int] = None
    ) -> Optional[Comment]:
        req = PreparedRequest(
            "PATCH", f"/comments/{comment_id}", json={"message": message, "spoiler": spoiler}
        )
        return self._model_opt(self._transport.request(req), Comment)

    def delete(self, comment_id: Any) -> bool:
        req = PreparedRequest("DELETE", f"/comments/{comment_id}")
        return self._bool(self._transport.request(req))

    def like(self, comment_id: Any, liked: bool = True) -> bool:
        req = PreparedRequest(
            "POST", f"/comments/{comment_id}/likes", json={"liked": liked}
        )
        return self._bool(self._transport.request(req))
