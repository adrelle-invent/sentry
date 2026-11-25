from typing import Any

from fastapi.datastructures import URL
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(100, ge=1, le=100)


class PaginatedResponse[T](PaginationParams):
    items: list[T]
    total: int = Field(
        ..., description="Total number of records matching criteria"
    )
    next: str | None
    prev: str | None
    has_more: bool


def build_pagination_meta(
    *,
    page: int,
    size: int,
    total: int,
    url: URL,
) -> dict[str, Any]:
    next_page = page + size if page + size < total else None
    prev_page = max(1, page - size) if page > 1 else None

    def cursor_url(new_page: int | None) -> str | None:
        if new_page is None:
            return None
        return str(url.include_query_params(page=new_page))

    return {
        "next": cursor_url(next_page),
        "prev": cursor_url(prev_page),
        "has_more": next_page is not None,
    }
