"""
Offset pagination that keeps list endpoints backwards compatible: the response body
stays a plain JSON array and the total row count is returned in `X-Total-Count`.
"""
from dataclasses import dataclass
from typing import List, Tuple, TypeVar

from fastapi import Query, Response
from sqlalchemy.orm import Query as SAQuery

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Rows per page"),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


def paginate(query: SAQuery, params: PageParams) -> Tuple[List, int]:
    """
    Run a page of `query` and its total count.
    The caller MUST have applied a deterministic ORDER BY (with a unique tie-breaker).
    """
    total = query.order_by(None).count()
    items = query.offset(params.offset).limit(params.page_size).all()
    return items, total


def set_total(response: Response, total: int) -> None:
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
