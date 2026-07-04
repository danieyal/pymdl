"""Subscription, flowers, awards, reports, calendar and leaderboard resources (spec §3)."""

from __future__ import annotations

from typing import Any, Union

from ..._request import PreparedRequest
from ...models.misc import (
    AwardResponse,
    Entries,
    Episodes,
    MySubscription,
    PersonGiftProcess,
    Quarter,
)
from .base import Resource

_LEADERBOARD_PERIODS = {0: "alltime", 1: "weekly", 2: "monthly"}


class SubscriptionResource(Resource):
    """MySubscriptionRepository."""

    def get(self) -> MySubscription:
        req = PreparedRequest("GET", "/subscriptions")
        return self._model(self._transport.request(req), MySubscription)


class FlowersResource(Resource):
    """SendFlowersRepository."""

    def gift_process(self, person_id: Any) -> PersonGiftProcess:
        req = PreparedRequest("GET", f"/people/{person_id}/gift_process")
        return self._model(self._transport.request(req), PersonGiftProcess)

    def top_senders(self, person_id: Any) -> Any:
        req = PreparedRequest("GET", f"/people/{person_id}/gifts")
        return self._raw(self._transport.request(req))

    def send(self, person_id: Any, amount: int) -> bool:
        req = PreparedRequest(
            "POST", f"/people/{person_id}/gift_process", json={"amount": amount}
        )
        return self._bool(self._transport.request(req))


class AwardsResource(Resource):
    """Awards listing and giving (TitleRepository)."""

    def list(self) -> AwardResponse:
        req = PreparedRequest("GET", "/awards")
        return self._model(self._transport.request(req), AwardResponse)

    def give(
        self,
        award_id: int,
        *,
        ref_id: Any,
        ref_type: str,
        ptype: str,
        pid: Any,
        anonymous: bool = False,
        private_message: str = "",
    ) -> bool:
        body = {
            "award_id": award_id,
            "ref_id": ref_id,
            "ref_type": ref_type,
            "ptype": ptype,
            "pid": pid,
            "anonymous": anonymous,
            "private_message": private_message,
        }
        req = PreparedRequest("POST", f"/awards/{award_id}", json=body)
        return self._bool(self._transport.request(req))


class ReportsResource(Resource):
    """Report rules and submission."""

    def rules(self, *, type: str = "comment") -> Any:
        req = PreparedRequest("GET", "/reports/rules", params={"type": type})
        return self._raw(self._transport.request(req))

    def submit(
        self, *, pid: int, ptype: str, comment: str, type: str, reason: str
    ) -> str:
        body = {"pid": pid, "ptype": ptype, "comment": comment, "type": type, "reason": reason}
        req = PreparedRequest("POST", "/reports", json=body)
        return self._str(self._transport.request(req))


class CalendarResource(Resource):
    """EpisodesRepository + QuarterlyRepository."""

    def episodes(self) -> Episodes:
        req = PreparedRequest("POST", "/calendar/episodes")
        return self._model(self._transport.request(req), Episodes)

    def quarter(self, *, year: int, quarter: Any) -> list[Quarter]:
        req = PreparedRequest(
            "POST", "/calendar/quarter", json={"year": year, "quarter": quarter}
        )
        return self._list(self._transport.request(req), Quarter)


class LeaderboardResource(Resource):
    """LeaderboardRepository."""

    def get(self, time_period: Union[int, str] = "alltime") -> list[Entries]:
        if isinstance(time_period, int):
            period = _LEADERBOARD_PERIODS.get(time_period, "monthly")
        else:
            period = time_period
        req = PreparedRequest(
            "GET", "/people/leaderboard", params={"time_period": period}
        )
        return self._list(self._transport.request(req), Entries, key="entries")
