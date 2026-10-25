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
    return await log_service.get_logs(
        db=db, pagination=pagination, filters=filters
    )


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


# @router.get(
#     "/stats",
# )
# @rate_limiter(limit=100, window=60)
# async def get_stats(request: Request, db: SessionDep):
#     return await LogService.get_stats(db)


# @router.get(
#     "/trends",
# )
# @rate_limiter(limit=100, window=60)
# async def get_trends(request: Request, db: SessionDep):
#     return await LogService.get_trends(db)


# @router.get(
#     "/issues",
# )
# @rate_limiter(limit=100, window=60)
# async def get_issues(request: Request, db: SessionDep):
#     return await LogService.get_issues(db)


# @router.get(
#     "/alerts",
# )
# @rate_limiter(limit=100, window=60)
# async def get_alerts(request: Request, db: SessionDep):
#     return await LogService.get_alerts(db)


# @router.get(
#     "/reports",
# )
# @rate_limiter(limit=100, window=60)
# async def get_reports(request: Request, db: SessionDep):
#     return await LogService.get_reports(db)
