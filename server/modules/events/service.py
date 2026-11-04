import hashlib
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.engine.result import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from core.cache import CacheDep
from core.database import SessionDep, TxSessionDep
from core.logger import get_logger
from modules.events.exceptions import EventNotFoundError
from modules.events.models import EventModel
from modules.events.schemas import EventCreate, Filters, Pagination

logger = get_logger(__name__)


class EventService:
    def __init__(self, cache: CacheDep) -> None:
        self.cache = cache

    # TODO: fix return type
    async def get_events(
        self, db: AsyncSession, filters: Filters, pagination: Pagination
    ) -> dict:
        async def _fetch_from_db():
            query: Select[tuple[EventModel]] = (
                select(EventModel)
                .order_by(EventModel.created_at.desc())
                .limit(pagination.limit)
                .offset(pagination.offset)
            )

            count_query = select(func.count()).select_from(EventModel)

            if filters.service:
                query = query.where(EventModel.service_id == filters.service)
                count_query = count_query.where(EventModel.service_id == filters.service)

            if filters.level:
                query = query.where(EventModel.level == filters.level)
                count_query = count_query.where(EventModel.level == filters.level)

            result: Result[tuple[EventModel]] = await db.execute(query)

            total_result = await db.execute(count_query)
            total = total_result.scalar_one()

            return {
                "data": [event.to_dict() for event in result.scalars().all()],
                "limit": pagination.limit,
                "offset": pagination.offset,
                "total": total,
            }

        return await self.cache.get_or_set_with_lock(
            f"events:service:{filters.service}:level:{filters.level}:limit:{pagination.limit}:offset:{pagination.offset}",
            _fetch_from_db,
        )

    async def get_event(self, db: SessionDep, event_id: str) -> dict:
        not_found_key = f"events:not_found:{event_id}"

        if await self.cache.has(not_found_key):
            raise EventNotFoundError(f"Event with id {event_id} not found")

        async def _fetch_from_db():
            result = await db.execute(
                select(EventModel).where(EventModel.id == event_id)
            )
            event = result.scalar_one_or_none()

            if not event:
                await self.cache.set(not_found_key, "1", expire_seconds=30)
                raise EventNotFoundError(f"Event with id {event_id} not found")

            return event.to_dict()

        return await self.cache.get_or_set_with_lock(
            f"event:{event_id}",
            _fetch_from_db,
            expire_seconds=60,
        )

    async def create_event(self, db: TxSessionDep, event_data: EventCreate) -> dict:
        # TODO: move to worker (batched)
        db.add(EventModel(**event_data.model_dump()))
        return {"status": "success", "queue_id": "msg_id"}

    async def get_stats(self, db: AsyncSession) -> dict:
        async def _fetch_from_db():
            result: Result[tuple[EventModel]] = await db.execute(select(EventModel))
            events = result.scalars().all()

            total_count = len(events)
            by_level: dict[str, int] = {}
            by_service: dict[str, int] = {}
            by_environment: dict[str, int] = {}

            for event in events:
                lvl = (event.level or "INFO").upper()
                svc = event.service_id or "unknown"
                env = getattr(event, "environment", "unknown")

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
            "events:stats",
            _fetch_from_db,
            expire_seconds=10,
        )

    async def get_trends(self, db: AsyncSession) -> list[dict]:
        async def _fetch_from_db():
            result: Result[tuple[EventModel]] = await db.execute(select(EventModel))
            events = result.scalars().all()

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

            for event in events:
                event_dt = event.created_at
                if not event_dt:
                    continue
                if isinstance(event_dt, str):
                    ts_str = event_dt
                    if ts_str.endswith("Z"):
                        ts_str = ts_str[:-1] + "+00:00"
                    try:
                        event_dt = datetime.fromisoformat(ts_str)
                    except Exception:
                        continue
                elif event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=UTC)

                diff = now - event_dt
                if diff.total_seconds() <= 24 * 3600:
                    key = event_dt.strftime("%Y-%m-%d %H:00")
                    if key in buckets:
                        lvl = (event.level or "INFO").upper()
                        buckets[key]["total_count"] += 1
                        if lvl in ("ERROR", "CRITICAL"):
                            buckets[key]["error_count"] += 1
                        elif lvl == "WARNING":
                            buckets[key]["warning_count"] += 1
                        else:
                            buckets[key]["info_count"] += 1

            return sorted(buckets.values(), key=lambda x: x["timestamp"])

        return await self.cache.get_or_set_with_lock(
            "events:trends",
            _fetch_from_db,
            expire_seconds=10,
        )

    async def get_issues(self, db: AsyncSession) -> list[dict]:
        async def _fetch_from_db():
            result: Result[tuple[EventModel]] = await db.execute(select(EventModel))
            events = result.scalars().all()

            groups: dict[str, dict] = {}

            def normalize_msg(msg: str) -> str:
                if not msg:
                    return "Empty event message"
                msg = re.sub(r"\d+", "X", msg)
                msg = re.sub(
                    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                    "UUID",
                    msg,
                )
                return msg.strip()

            for event in events:
                svc = event.service or "unknown"
                lvl = (event.level or "INFO").upper()
                env = event.environment or "unknown"
                raw_msg = event.event_message or ""
                norm_msg = normalize_msg(raw_msg)

                key = f"{svc}:{lvl}:{env}:{norm_msg}"
                created_at = (
                    event.created_at.isoformat()
                    if isinstance(event.created_at, datetime)
                    else str(event.created_at)
                    if event.created_at
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
            "events:issues",
            _fetch_from_db,
            expire_seconds=10,
        )

    # --------------------------------------------------------------------------
    # Legacy commented-out static methods (kept for reference)
    # --------------------------------------------------------------------------
    # @staticmethod
    # async def get_stats(db: AsyncSession) -> dict:
    #     cached_data = await Cache.get("events:stats")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(EventModel)
    #     result = await db.execute(query)
    #     events = result.scalars().all()

    #     total_count = len(events)
    #     by_level: dict[str, int] = {}
    #     by_service: dict[str, int] = {}
    #     by_environment: dict[str, int] = {}

    #     for event in events:
    #         lvl = (event.level or "INFO").upper()
    #         svc = event.service or "unknown"
    #         env = event.environment or "unknown"

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

    #     await Cache.set("events:stats", json.dumps(stats), expire_seconds=10)
    #     return stats

    # @staticmethod
    # async def get_trends(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("events:trends")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(EventModel)
    #     result = await db.execute(query)
    #     events = result.scalars().all()

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

    #     for event in events:
    #         event_dt = event.created_at
    #         if not event_dt:
    #             continue
    #         if isinstance(event_dt, str):
    #             ts_str = event_dt
    #             if ts_str.endswith("Z"):
    #                 ts_str = ts_str[:-1] + "+00:00"
    #             try:
    #                 event_dt = datetime.fromisoformat(ts_str)
    #             except Exception:
    #                 continue
    #         elif event_dt.tzinfo is None:
    #             event_dt = event_dt.replace(tzinfo=UTC)

    #         diff = now - event_dt
    #         if diff.total_seconds() <= 24 * 3600:
    #             key = event_dt.strftime("%Y-%m-%d %H:00")
    #             if key in buckets:
    #                 lvl = (event.level or "INFO").upper()
    #                 buckets[key]["total_count"] += 1
    #                 if lvl in ("ERROR", "CRITICAL"):
    #                     buckets[key]["error_count"] += 1
    #                 elif lvl == "WARNING":
    #                     buckets[key]["warning_count"] += 1
    #                 else:
    #                     buckets[key]["info_count"] += 1

    #     sorted_buckets = sorted(buckets.values(), key=lambda x: x["timestamp"])
    #     await Cache.set(
    #         "events:trends", json.dumps(sorted_buckets), expire_seconds=10
    #     )
    #     return sorted_buckets

    # @staticmethod
    # async def get_issues(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("events:issues")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(EventModel)
    #     result = await db.execute(query)
    #     events = result.scalars().all()

    #     groups: dict[str, dict] = {}

    #     def normalize_msg(msg: str) -> str:
    #         if not msg:
    #             return "Empty event message"
    #         msg = re.sub(r"\d+", "X", msg)
    #         msg = re.sub(
    #             r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    #             "UUID",
    #             msg,
    #         )
    #         return msg.strip()

    #     for event in events:
    #         svc = event.service or "unknown"
    #         lvl = (event.level or "INFO").upper()
    #         env = event.environment or "unknown"
    #         raw_msg = event.event_message or ""
    #         norm_msg = normalize_msg(raw_msg)

    #         key = f"{svc}:{lvl}:{env}:{norm_msg}"
    #         created_at = (
    #             event.created_at.isoformat()
    #             if isinstance(event.created_at, datetime)
    #             else str(event.created_at)
    #             if event.created_at
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
    #         "events:issues", json.dumps(issues_list), expire_seconds=10
    #     )
    #     return issues_list

    # @staticmethod
    # async def get_alerts(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("events:alerts")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     query = select(EventModel)
    #     result = await db.execute(query)
    #     events = result.scalars().all()

    #     now = datetime.now(UTC)
    #     error_counts: dict[str, int] = {}

    #     for event in events:
    #         lvl = (event.level or "INFO").upper()
    #         if lvl not in ("ERROR", "CRITICAL"):
    #             continue

    #         event_dt = event.created_at
    #         if not event_dt:
    #             continue
    #         if isinstance(event_dt, str):
    #             ts_str = event_dt
    #             if ts_str.endswith("Z"):
    #                 ts_str = ts_str[:-1] + "+00:00"
    #             try:
    #                 event_dt = datetime.fromisoformat(ts_str)
    #             except Exception:
    #                 continue
    #         elif event_dt.tzinfo is None:
    #             event_dt = event_dt.replace(tzinfo=UTC)

    #         diff = now - event_dt
    #         if diff.total_seconds() <= 15 * 60:
    #             svc = event.service or "unknown"
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

    #     await Cache.set("events:alerts", json.dumps(alerts), expire_seconds=10)
    #     return alerts

    # @staticmethod
    # async def get_reports(db: AsyncSession) -> list[dict]:
    #     cached_data = await Cache.get("events:reports")
    #     if cached_data:
    #         return json.loads(cached_data)

    #     stats = await EventService.get_stats(db)
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

    #     await Cache.set("events:reports", json.dumps(reports), expire_seconds=10)
    #     return reports
