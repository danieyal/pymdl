"""Shared Pydantic base and reusable field helpers.

Because the wire schema is reverse-engineered and drifts between app builds, every model
tolerates unknown keys (``extra="ignore"``) and accepts either the field name or its wire
alias (``populate_by_name=True``).
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from ..config import IMAGE_HOST


class MDLModel(BaseModel):
    """Base for every model in this package."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        str_strip_whitespace=False,
        arbitrary_types_allowed=True,
    )


def resolve_image_url(value: Optional[str]) -> Optional[str]:
    """Prefix a relative image path with the image host (spec: ``getCurrentProfile``)."""
    if not value:
        return value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    if value.startswith("//"):
        return f"https:{value}"
    return f"{IMAGE_HOST}/{value.lstrip('/')}"


class Images(MDLModel):
    """Shared image object (``models/image.dart``): ``thumb``, ``medium``, ``poster``."""

    thumb: Optional[str] = None
    medium: Optional[str] = None
    poster: Optional[str] = None


class SearchEntry(MDLModel):
    """A ``{name, id}`` pair used for genres, tags, alt titles, etc."""

    id: Optional[int] = None
    name: Optional[str] = None


def as_int_flag(value: Any) -> Optional[int]:
    """Coerce a truthy/int watch-status style value to an int, tolerating dict wrappers."""
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("status")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
