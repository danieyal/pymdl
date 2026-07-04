"""Lightweight pagination container.

Most list endpoints accept ``page`` / ``limit`` query params and return a bare list;
a few expose the grand total via the ``x-pagination-total`` response header
(e.g. ``getTotalCommentCount``). :class:`Page` carries the parsed items alongside that
total and the current page so callers can drive their own paging loops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Iterator, List, Optional, TypeVar

T = TypeVar("T")

#: Header the API uses to report the total count of a paginated collection.
PAGINATION_TOTAL_HEADER = "x-pagination-total"


@dataclass
class Page(Generic[T]):
    items: List[T]
    page: int
    total: Optional[int] = None

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    @property
    def is_empty(self) -> bool:
        return not self.items
