"""Typed helpers for raw pymongo access from repositories."""

from typing import Any, cast

from beanie import Document
from pymongo.asynchronous.collection import AsyncCollection


def raw_collection(model: type[Document]) -> AsyncCollection[dict[str, Any]]:
    """Return the raw async pymongo collection for a Beanie model, fully typed.

    Centralises the single unavoidable pyright ignore: Beanie's
    ``get_pymongo_collection`` member is only partially typed upstream.
    """
    return cast(
        "AsyncCollection[dict[str, Any]]",
        model.get_pymongo_collection(),  # pyright: ignore[reportUnknownMemberType]
    )
