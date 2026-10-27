import hashlib
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from app.core.cache import CacheDep
from app.core.database import SessionDep, TxSessionDep
from app.core.logger import get_logger
from app.modules.logs.exceptions import LogNotFoundError
from app.modules.logs.models import LogModel
from app.modules.logs.schemas import Filters, LogCreate, Pagination

logger = get_logger(__name__)


class LogService:
    def __init__(self, cache: CacheDep) -> None:
        self.cache = cache

    # TODO: fix return type
    async def get_logs(
        self, db: AsyncSession, filters: Filters, pagination: Pagination
    ) -> dict:
        async def _fetch_from_db():
            query: Select[tuple[LogModel]] = (
                select(LogModel)
                .order_by(LogModel.created_at.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )

            count_query = select(func.count()).select_from(LogModel)

            if filters.service:
                query = query.where(LogModel.service == filters.service)
                count_query = count_query.where(LogModel.service == filters.service)

            if filters.level:
                query = query.where(LogModel.level == filters.level)
                count_query = count_query.where(LogModel.level == filters.level)

            result: Result[tuple[LogModel]] = await db.execute(query)

            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            return {
                "data": [log.to_dict() for log in result.scalars().all()],
                "limit": pagination.limit,
                "offset": pagination.offset,
                "total": total,
            }

        return await self.cache.get_or_set_with_lock(
            f"logs:service:{filters.service}:level:{filters.level}:limit:{pagination.limit}:offset:{pagination.offset}",
            _fetch_from_db,
        )

    async def get_log(self, db: SessionDep, log_id: str) -> dict:
        not_found_key = f"logs:not_found:{log_id}"

        if await self.cache.has(not_found_key):
            raise LogNotFoundError(f"Log with id {log_id} not found")

        async def _fetch_from_db():
            result = await db.execute(
                select(LogModel).where(LogModel.id == log_id)
            )
            log = result.scalar_one_or_none()

            if not log:
                await self.cache.set(not_found_key, "1", expire_seconds=30)
                raise LogNotFoundError(f"Log with id {log_id} not found")

            return log.to_dict()

        return await self.cache.get_or_set_with_lock(
            f"log:{log_id}",
            _fetch_from_db,
            expire_seconds=60,
        )

    async def create_log(self, db: TxSessionDep, log_data: LogCreate) -> dict:
        # TODO: move to worker (batched)
        db.add(LogModel(**log_data.model_dump()))
        return {"status": "success", "queue_id": "msg_id"}

    async def get_stats(self, db: AsyncSession) -> dict:
        async def _fetch_from_db():
            result: Result[tuple[LogModel]] = await db.execute(select(LogModel))
            logs = result.scalars().all()

            total_count = len(logs)
            by_level: dict[str, int] = {}
            by_service: dict[str, int] = {}
            by_environment: dict[str, int] = {}

            for log in logs:
                lvl = (log.level or "INFO").upper()
                svc = log.service or "unknown"
                env = log.environment or "unknown"

                by_level[lvl] = by_level.get(lvl, 0) + 1
                by_service[svc] = by_service.get(svc, 0) + 1
                by_environment[env] = by_environment.get(env, 0) + 1

            error_count = by_level.get("ERROR", 0) + by_level.get("CRITICAL", 0)
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0.0

            return {
                "total_count": total_count,
                "by_level": by_level,
                "by_service": by_service,
                "by_environment": by_environment,
                "error_rate": round(error_rate, 2),
            }

        return await self.cache.get_or_set_with_lock(
            "logs:stats",
            _fetch_from_db,
            expire_seconds=10,
        )

    async def get_trends(self, db: AsyncSession) -> list[dict]:
        async def _fetch_from_db():
            result: Result[tuple[LogModel]] = await db.execute(select(LogModel))
            logs = result.scalars().all()

            now = datetime.now(UTC)
            buckets: dict[str, dict] = {}
            for i in range(24):
                dt = now - timedelta(hours=i)
                key = dt.strftime("%Y-%m-%d %H:00")
                buckets[key] = {
                    "timestamp": key,
                    "info_count": 0,
                    "warning_count": 0,
                    "error_count": 0,
                    "total_count": 0,
                }

            for log in logs:
                log_dt = log.created_at
                if not log_dt:
                    continue
                if isinstance(log_dt, str):
                    ts_str = log_dt
                    if ts_str.endswith("Z"):
                        ts_str = ts_str[:-1] + "+00:00"
                    try:
                        log_dt = datetime.fromisoformat(ts_str)
                    except Exception:
                        continue
                elif log_dt.tzinfo is None:
                    log_dt = log_dt.replace(tzinfo=UTC)

                diff = now - log_dt
                if diff.total_seconds() <= 24 * 3600:
                    key = log_dt.strftime("%Y-%m-%d %H:00")
                    if key in buckets:
                        lvl = (log.level or "INFO").upper()
                        buckets[key]["total_count"] += 1
                        if lvl in ("ERROR", "CRITICAL"):
                            buckets[key]["error_count"] += 1
                        elif lvl == "WARNING":
                            buckets[key]["warning_count"] += 1
                        else:
                            buckets[key]["info_count"] += 1

            return sorted(buckets.values(), key=lambda x: x["timestamp"])

        return await self.cache.get_or_set_with_lock(
            "logs:trends",
            _fetch_from_db,
            expire_seconds=10,
        )

    async def get_issues(self, db: AsyncSession) -> list[dict]:
        async def _fetch_from_db():
            result: Result[tuple[LogModel]] = await db.execute(select(LogModel))
            logs = result.scalars().all()

            groups: dict[str, dict] = {}

            def normalize_msg(msg: str) -> str:
                if not msg:
                    return "Empty log message"
                msg = re.sub(r"\d+", "X", msg)
                msg = re.sub(
                    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                    "UUID",
                    msg,
                )
                return msg.strip()

            for log in logs:
                svc = log.service or "unknown"
                lvl = (log.level or "INFO").upper()
                env = log.environment or "unknown"
                raw_msg = log.log_message or ""
                norm_msg = normalize_msg(raw_msg)

                key = f"{svc}:{lvl}:{env}:{norm_msg}"
                created_at = (
                    log.created_at.isoformat()
                    if isinstance(log.created_at, datetime)
                    else str(log.created_at)
                    if log.created_at
                    else None
                )

                if key not in groups:
                    issue_id = hashlib.md5(key.encode()).hexdigest()
                    groups[key] = {
                        "id": f"iss_{issue_id[:12]}",
                        "service": svc,
                        "level": lvl,
                        "environment": env,
                        "message": raw_msg if len(raw_msg) < 100 else raw_msg[:97] + "...",
                        "count": 0,
                        "first_seen": created_at,
                        "last_seen": created_at,
                        "status": "Active" if lvl in ("ERROR", "CRITICAL") else "Monitored",
                        "assigned_to": "Unassigned",
                    }

                group = groups[key]
                group["count"] += 1
                if created_at:
                    if not group["first_seen"] or created_at < group["first_seen"]:
                        group["first_seen"] = created_at
                    if not group["last_seen"] or created_at > group["last_seen"]:
                        group["last_seen"] = created_at

            return list(groups.values())

        return await self.cache.get_or_set_with_lock(
            "logs:issues",
            _fetch_from_db,
            expire_seconds=10,
        )

    # --------------------------------------------------------------------------
    # Legacy commented-out static methods (kept for reference)
    # --------------------------------------------------------------------------
    # @staticmethod
    # async def get_stats(db: AsyncSession) -> dict:
    #     cached_data = await Cache.get("logs:stats")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(LogModel)
    #     result = await db.execute(query)
    #     logs = result.scalars().all()

    #     total_count = len(logs)
    #     by_level: dict[str, int] = {}
    #     by_service: dict[str, int] = {}
    #     by_environment: dict[str, int] = {}

    #     for log in logs:
    #         lvl = (log.level or "INFO").upper()
    #         svc = log.service or "unknown"
    #         env = log.environment or "unknown"

    #         by_level[lvl] = by_level.get(lvl, 0) + 1
    #         by_service[svc] = by_service.get(svc, 0) + 1
    #         by_environment[env] = by_environment.get(env, 0) + 1

    #     error_count = by_level.get("ERROR", 0) + by_level.get("CRITICAL", 0)
    #     error_rate = (
    #         (error_count / total_count * 100) if total_count > 0 else 0.0
    #     )

    #     stats = {
    #         "total_count": total_count,
    #         "by_level": by_level,
    #         "by_service": by_service,
    #         "by_environment": by_environment,
    #         "error_rate": round(error_rate, 2),
    #     }

    #     await Cache.set("logs:stats", json.dumps(stats), expire_seconds=10)
    #     return stats

    # @staticmethod
    # async def get_trends(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("logs:trends")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(LogModel)
    #     result = await db.execute(query)
    #     logs = result.scalars().all()

    #     now = datetime.now(UTC)
    #     buckets: dict[str, dict] = {}
    #     for i in range(24):
    #         dt = now - timedelta(hours=i)
    #         key = dt.strftime("%Y-%m-%d %H:00")
    #         buckets[key] = {
    #             "timestamp": key,
    #             "info_count": 0,
    #             "warning_count": 0,
    #             "error_count": 0,
    #             "total_count": 0,
    #         }

    #     for log in logs:
    #         log_dt = log.created_at
    #         if not log_dt:
    #             continue
    #         if isinstance(log_dt, str):
    #             ts_str = log_dt
    #             if ts_str.endswith("Z"):
    #                 ts_str = ts_str[:-1] + "+00:00"
    #             try:
    #                 log_dt = datetime.fromisoformat(ts_str)
    #             except Exception:
    #                 continue
    #         elif log_dt.tzinfo is None:
    #             log_dt = log_dt.replace(tzinfo=UTC)

    #         diff = now - log_dt
    #         if diff.total_seconds() <= 24 * 3600:
    #             key = log_dt.strftime("%Y-%m-%d %H:00")
    #             if key in buckets:
    #                 lvl = (log.level or "INFO").upper()
    #                 buckets[key]["total_count"] += 1
    #                 if lvl in ("ERROR", "CRITICAL"):
    #                     buckets[key]["error_count"] += 1
    #                 elif lvl == "WARNING":
    #                     buckets[key]["warning_count"] += 1
    #                 else:
    #                     buckets[key]["info_count"] += 1

    #     sorted_buckets = sorted(buckets.values(), key=lambda x: x["timestamp"])
    #     await Cache.set(
    #         "logs:trends", json.dumps(sorted_buckets), expire_seconds=10
    #     )
    #     return sorted_buckets

    # @staticmethod
    # async def get_issues(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("logs:issues")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(LogModel)
    #     result = await db.execute(query)
    #     logs = result.scalars().all()

    #     groups: dict[str, dict] = {}

    #     def normalize_msg(msg: str) -> str:
    #         if not msg:
    #             return "Empty log message"
    #         msg = re.sub(r"\d+", "X", msg)
    #         msg = re.sub(
    #             r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    #             "UUID",
    #             msg,
    #         )
    #         return msg.strip()

    #     for log in logs:
    #         svc = log.service or "unknown"
    #         lvl = (log.level or "INFO").upper()
    #         env = log.environment or "unknown"
    #         raw_msg = log.log_message or ""
    #         norm_msg = normalize_msg(raw_msg)

    #         key = f"{svc}:{lvl}:{env}:{norm_msg}"
    #         created_at = (
    #             log.created_at.isoformat()
    #             if isinstance(log.created_at, datetime)
    #             else str(log.created_at)
    #             if log.created_at
    #             else None
    #         )

    #         if key not in groups:
    #             issue_id = hashlib.md5(key.encode()).hexdigest()
    #             groups[key] = {
    #                 "id": f"iss_{issue_id[:12]}",
    #                 "service": svc,
    #                 "level": lvl,
    #                 "environment": env,
    #                 "message": raw_msg
    #                 if len(raw_msg) < 100
    #                 else raw_msg[:97] + "...",
    #                 "count": 0,
    #                 "first_seen": created_at,
    #                 "last_seen": created_at,
    #                 "status": "Active"
    #                 if lvl in ("ERROR", "CRITICAL")
    #                 else "Monitored",
    #                 "assigned_to": "Unassigned",
    #             }

    #         group = groups[key]
    #         group["count"] += 1
    #         if created_at:
    #             if not group["first_seen"] or created_at < group["first_seen"]:
    #                 group["first_seen"] = created_at
    #             if not group["last_seen"] or created_at > group["last_seen"]:
    #                 group["last_seen"] = created_at

    #     issues_list = list(groups.values())
    #     await Cache.set(
    #         "logs:issues", json.dumps(issues_list), expire_seconds=10
    #     )
    #     return issues_list

    # @staticmethod
    # async def get_alerts(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("logs:alerts")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(LogModel)
    #     result = await db.execute(query)
    #     logs = result.scalars().all()

    #     now = datetime.now(UTC)
    #     error_counts: dict[str, int] = {}

    #     for log in logs:
    #         lvl = (log.level or "INFO").upper()
    #         if lvl not in ("ERROR", "CRITICAL"):
    #             continue

    #         log_dt = log.created_at
    #         if not log_dt:
    #             continue
    #         if isinstance(log_dt, str):
    #             ts_str = log_dt
    #             if ts_str.endswith("Z"):
    #                 ts_str = ts_str[:-1] + "+00:00"
    #             try:
    #                 log_dt = datetime.fromisoformat(ts_str)
    #             except Exception:
    #                 continue
    #         elif log_dt.tzinfo is None:
    #             log_dt = log_dt.replace(tzinfo=UTC)

    #         diff = now - log_dt
    #         if diff.total_seconds() <= 15 * 60:
    #             svc = log.service or "unknown"
    #             error_counts[svc] = error_counts.get(svc, 0) + 1

    #     alerts = []
    #     for svc, count in error_counts.items():
    #         if count >= 3:
    #             alert_id = hashlib.md5(f"{svc}:{count}".encode()).hexdigest()[
    #                 :12
    #             ]
    #             alerts.append(
    #                 {
    #                     "id": f"alt_{alert_id}",
    #                     "service": svc,
    #                     "title": "High Error Rate",
    #                     "description": f"Service '{svc}' generated {count} errors in the last 15 minutes.",
    #                     "severity": "CRITICAL" if count >= 5 else "WARNING",
    #                     "timestamp": now.isoformat(),
    #                     "status": "Active",
    #                 }
    #             )

    #     await Cache.set("logs:alerts", json.dumps(alerts), expire_seconds=10)
    #     return alerts

    # @staticmethod
    # async def get_reports(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("logs:reports")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     stats = await LogService.get_stats(db)
    #     total_events = stats["total_count"]
    #     error_rate = stats["error_rate"]

    #     uptime_api = max(95.0, round(100.0 - error_rate * 0.5, 2))
    #     uptime_db = 99.99

    #     now = datetime.now(UTC)

    #     reports = [
    #         {
    #             "id": "rep_today",
    #             "title": "Daily Reliability Report",
    #             "period": now.strftime("%Y-%m-%d"),
    #             "total_events": total_events,
    #             "incidents_count": 1 if error_rate > 5.0 else 0,
    #             "avg_mttr": "12m" if error_rate > 0 else "0m",
    #             "service_uptime": {
    #                 "api-gateway": f"{uptime_api}%",
    #                 "database": f"{uptime_db}%",
    #                 "auth-service": "100%",
    #             },
    #             "summary": f"System operations normal. Service error rate is at {error_rate}%. "
    #             f"Uptime remains within SLA guidelines.",
    #         },
    #         {
    #             "id": "rep_weekly",
    #             "title": "Weekly Observability Summary",
    #             "period": f"{(now - timedelta(days=7)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
    #             "total_events": total_events * 5,
    #             "incidents_count": 3 if error_rate > 5.0 else 1,
    #             "avg_mttr": "15m",
    #             "service_uptime": {
    #                 "api-gateway": f"{max(98.0, uptime_api)}%",
    #                 "database": "99.95%",
    #                 "auth-service": "99.98%",
    #             },
    #             "summary": "Weekly audit completed. Major services showed robust uptime. Cache-hit ratio was 94.2%.",
    #         },
    #     ]

    #     await Cache.set("logs:reports", json.dumps(reports), expire_seconds=10)
    #     return reports
