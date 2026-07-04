"""Base resource with response-parsing helpers shared by every resource group.

All helpers here are pure (no ``await``) so they pass through unasync unchanged.
"""

from __future__ import annotations

from typing import Any, Optional, TypeVar

from ..._request import TransportResponse
from ...models.base import MDLModel
from ...pagination import PAGINATION_TOTAL_HEADER, Page
from .._transport import AsyncTransport

M = TypeVar("M", bound=MDLModel)


class AsyncResource:
    """Base class holding the transport and JSON→model parsing helpers."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    # --- parsing helpers -------------------------------------------------

    @staticmethod
    def _model(resp: TransportResponse, model: type[M]) -> M:
        return model.model_validate(resp.json)

    @staticmethod
    def _model_opt(resp: TransportResponse, model: type[M]) -> Optional[M]:
        if resp.json in (None, "", [], {}):
            return None
        return model.model_validate(resp.json)

    @staticmethod
    def _list(
        resp: TransportResponse, model: type[M], key: Optional[str] = None
    ) -> list[M]:
        data: Any = resp.json
        if key is not None and isinstance(data, dict):
            data = data.get(key)
        if not isinstance(data, list):
            return []
        return [model.model_validate(item) for item in data]

    @staticmethod
    def _page(
        resp: TransportResponse, model: type[M], page: int, key: Optional[str] = None
    ) -> Page[M]:
        items = AsyncResource._list(resp, model, key=key)
        total_raw = resp.headers.get(PAGINATION_TOTAL_HEADER)
        total = int(total_raw) if total_raw and total_raw.isdigit() else None
        return Page(items=items, page=page, total=total)

    @staticmethod
    def _bool(resp: TransportResponse) -> bool:
        data = resp.json
        if isinstance(data, bool):
            return data
        if isinstance(data, dict):
            for key in ("success", "result", "ok"):
                if isinstance(data.get(key), bool):
                    return bool(data[key])
        return 200 <= resp.status_code < 300

    @staticmethod
    def _str(resp: TransportResponse) -> str:
        data = resp.json
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for key in ("message", "result", "status"):
                if isinstance(data.get(key), str):
                    return str(data[key])
        return resp.text

    @staticmethod
    def _int(resp: TransportResponse, key: Optional[str] = None) -> int:
        data: Any = resp.json
        if key is not None and isinstance(data, dict):
            data = data.get(key)
        if isinstance(data, bool):
            return int(data)
        if isinstance(data, (int, float)):
            return int(data)
        if isinstance(data, str):
            try:
                return int(data.strip())
            except ValueError:
                return 0
        return 0

    @staticmethod
    def _raw(resp: TransportResponse) -> Any:
        return resp.json
