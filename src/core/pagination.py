"""Pagination utilities for API list endpoints."""
from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def paginate_query(
    stmt: Any,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[Any, int, int]:
    """Apply pagination to a SQL statement.

    Returns (paginated_stmt, offset, limit).
    """
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    offset = max((page - 1) * page_size, 0)
    return stmt.offset(offset).limit(page_size), offset, page_size


def build_paginated_response(
    items: list[T],
    page: int,
    page_size: int,
    total_count: int | None = None,
) -> dict[str, Any]:
    """Build a standard paginated response dict."""
    total = total_count if total_count is not None else len(items)
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }


def get_page_params(
    page: int | None = None,
    page_size: int | None = None,
) -> tuple[int, int]:
    """Extract and validate page params from request."""
    page = max(page or 1, 1)
    page_size = min(max(page_size or DEFAULT_PAGE_SIZE, 1), MAX_PAGE_SIZE)
    return page, page_size
