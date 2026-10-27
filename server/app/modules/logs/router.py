from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.database import SessionDep, TxSessionDep
from app.modules.logs.schemas import Filters, LogCreate, LogResponse, Pagination
from app.modules.logs.service import LogService

router = APIRouter(prefix="/v1/logs", tags=["logs"])

LogServiceDep = Annotated[LogService, Depends()]


# TODO: fix response_model
@router.get("")
async def index(
    request: Request,
    db: SessionDep,
    log_service: LogServiceDep,
    pagination: Annotated[Pagination, Query()],
    filters: Annotated[Filters, Query()],
):
    result = await log_service.get_logs(
        db=db, pagination=pagination, filters=filters
    )

    offset, limit, total = result["offset"], result["limit"], result["total"]
    next_offset = offset + limit if offset + limit < total else None
    prev_offset = max(0, offset - limit) if offset > 0 else None

    def cursor_url(new_offset: int | None) -> str | None:
        if new_offset is None:
            return None
        return str(request.url.include_query_params(offset=new_offset))

    return {
        **result,
        "next": cursor_url(next_offset),
        "prev": cursor_url(prev_offset),
    }


@router.get("/stats")
async def get_stats(
    request: Request,
    db: SessionDep,
    log_service: LogServiceDep,
):
    return await log_service.get_stats(db=db)


@router.get("/trends")
async def get_trends(
    request: Request,
    db: SessionDep,
    log_service: LogServiceDep,
):
    return await log_service.get_trends(db=db)


@router.get("/issues")
async def get_issues(
    request: Request,
    db: SessionDep,
    log_service: LogServiceDep,
):
    return await log_service.get_issues(db=db)


@router.get("/{log_id}", response_model=LogResponse)
async def show(
    request: Request,
    db: SessionDep,
    log_service: LogServiceDep,
    log_id: str,
):
    return await log_service.get_log(db=db, log_id=log_id)


@router.post("", status_code=status.HTTP_201_CREATED)
async def store(
    request: Request,
    db: TxSessionDep,
    log_service: LogServiceDep,
    log: LogCreate,
):
    return await log_service.create_log(db=db, log_data=log)
