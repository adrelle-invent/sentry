from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.modules.logs.schemas import LogCreate, LogResponse
from app.modules.logs.service import LogService

router = APIRouter(prefix="/v1/logs", tags=["logs"])

LogServiceDep = Annotated[LogService, Depends()]


@router.get("", response_model=list[LogResponse])
async def index(
    request: Request,
    log_service: LogServiceDep,
    service: str | None = None,
    level: str | None = None,
):
    return await log_service.get_logs(service, level)


@router.get("/{log_id}", response_model=LogResponse)
async def show(
    request: Request,
    log_service: LogServiceDep,
    log_id: str,
):
    return await log_service.get_log(log_id)


@router.post("", response_model=LogResponse)
async def store(
    request: Request,
    log_service: LogServiceDep,
    log: LogCreate,
):
    return await log_service.create_log(log)


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
