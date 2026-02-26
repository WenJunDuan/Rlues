"""PostgreSQL store backend for adapter persistence.

Uses psycopg (v3) for sync access. Auto-creates tables on first connect.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .store import StoreBackend

logger = logging.getLogger("adapter.store_postgres")


_DDL = """
CREATE TABLE IF NOT EXISTS adapter_tasks (
    task_id     TEXT PRIMARY KEY,
    command     TEXT NOT NULL,
    tenant_id   TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    envelope    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS adapter_results (
    task_id   TEXT PRIMARY KEY REFERENCES adapter_tasks(task_id) ON DELETE CASCADE,
    status    TEXT NOT NULL,
    result    JSONB NOT NULL DEFAULT '{}',
    execution JSONB NOT NULL DEFAULT '{}',
    error     JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS adapter_task_meta (
    task_id          TEXT PRIMARY KEY REFERENCES adapter_tasks(task_id) ON DELETE CASCADE,
    command          TEXT,
    tenant_id        TEXT,
    operator_id      TEXT,
    session_key      TEXT,
    status           TEXT NOT NULL DEFAULT 'queued',
    decision         TEXT,
    owner_api_key_hash TEXT,
    created_at       TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ,
    started_at       TIMESTAMPTZ,
    finished_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS adapter_events (
    id        BIGSERIAL PRIMARY KEY,
    task_id   TEXT NOT NULL,
    event_type TEXT NOT NULL,
    data      JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_adapter_events_task ON adapter_events(task_id);

CREATE TABLE IF NOT EXISTS adapter_history_logs (
    id        BIGSERIAL PRIMARY KEY,
    action    TEXT NOT NULL,
    task_id   TEXT,
    payload   JSONB NOT NULL DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_adapter_history_task ON adapter_history_logs(task_id);
"""


class PostgresStoreBackend(StoreBackend):
    """PostgreSQL-backed store using psycopg (v3 sync)."""

    def __init__(self, config: Dict[str, Any]) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "psycopg is required for postgres backend: pip install psycopg[binary]"
            ) from exc

        conninfo = psycopg.conninfo.make_conninfo(
            host=config.get("host", "localhost"),
            port=int(config.get("port", 5432)),
            dbname=config.get("database", "adapter"),
            user=config.get("user", "adapter"),
            password=config.get("password", ""),
        )
        pool_size = int(config.get("pool_size", 5))

        from psycopg_pool import ConnectionPool  # type: ignore

        self._pool = ConnectionPool(conninfo=conninfo, min_size=1, max_size=pool_size)
        self._init_tables()

    def _init_tables(self) -> None:
        try:
            with self._pool.connection() as conn:
                conn.execute(_DDL)
                conn.commit()
            logger.info("postgres tables initialized")
        except Exception:
            logger.exception("failed to initialize postgres tables")
            raise

    def _conn(self):
        return self._pool.connection()

    # ── Task envelope ──

    def save_task(self, task_id: str, envelope: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adapter_tasks (task_id, command, tenant_id, operator_id, payload, envelope)
                   VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
                   ON CONFLICT (task_id) DO UPDATE SET envelope = EXCLUDED.envelope""",
                (
                    task_id,
                    envelope.get("command", ""),
                    envelope.get("context", {}).get("tenant_id", ""),
                    envelope.get("context", {}).get("operator_id", ""),
                    json.dumps(envelope.get("payload", {}), ensure_ascii=False),
                    json.dumps(envelope, ensure_ascii=False),
                ),
            )
            conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT envelope FROM adapter_tasks WHERE task_id = %s", (task_id,)
            ).fetchone()
        if row is None:
            return None
        data = row[0]
        return data if isinstance(data, dict) else json.loads(data)

    def has_task(self, task_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM adapter_tasks WHERE task_id = %s", (task_id,)
            ).fetchone()
        return row is not None

    # ── Result envelope ──

    def save_result(self, task_id: str, result: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adapter_results (task_id, status, result, execution, error)
                   VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
                   ON CONFLICT (task_id) DO UPDATE SET
                     status = EXCLUDED.status,
                     result = EXCLUDED.result,
                     execution = EXCLUDED.execution,
                     error = EXCLUDED.error""",
                (
                    task_id,
                    result.get("status", ""),
                    json.dumps(result.get("result", {}), ensure_ascii=False),
                    json.dumps(result.get("execution", {}), ensure_ascii=False),
                    json.dumps(result.get("error"), ensure_ascii=False) if result.get("error") else None,
                ),
            )
            conn.commit()

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT task_id, status, result, execution, error FROM adapter_results WHERE task_id = %s",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "task_id": row[0],
            "status": row[1],
            "result": row[2] if isinstance(row[2], dict) else json.loads(row[2]),
            "execution": row[3] if isinstance(row[3], dict) else json.loads(row[3]),
            "error": (row[4] if isinstance(row[4], dict) else json.loads(row[4])) if row[4] else None,
        }

    def has_result(self, task_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM adapter_results WHERE task_id = %s", (task_id,)
            ).fetchone()
        return row is not None

    # ── Task meta ──

    def save_meta(self, task_id: str, meta: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adapter_task_meta
                     (task_id, command, tenant_id, operator_id, session_key,
                      status, decision, owner_api_key_hash,
                      created_at, updated_at, started_at, finished_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (task_id) DO UPDATE SET
                     status = EXCLUDED.status,
                     decision = EXCLUDED.decision,
                     updated_at = EXCLUDED.updated_at,
                     started_at = EXCLUDED.started_at,
                     finished_at = EXCLUDED.finished_at""",
                (
                    task_id,
                    meta.get("command"),
                    meta.get("tenant_id"),
                    meta.get("operator_id"),
                    meta.get("session_key"),
                    meta.get("status", "queued"),
                    meta.get("decision"),
                    meta.get("owner_api_key_hash"),
                    meta.get("created_at"),
                    meta.get("updated_at"),
                    meta.get("started_at"),
                    meta.get("finished_at"),
                ),
            )
            conn.commit()

    def get_meta(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                """SELECT task_id, command, tenant_id, operator_id, session_key,
                          status, decision, owner_api_key_hash,
                          created_at, updated_at, started_at, finished_at
                   FROM adapter_task_meta WHERE task_id = %s""",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        cols = [
            "task_id", "command", "tenant_id", "operator_id", "session_key",
            "status", "decision", "owner_api_key_hash",
            "created_at", "updated_at", "started_at", "finished_at",
        ]
        result = {}
        for i, col in enumerate(cols):
            val = row[i]
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col] = val
        return result

    def list_meta(
        self,
        *,
        command: Optional[str] = None,
        tenant_id: Optional[str] = None,
        operator_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        conditions = []
        params: list = []
        if command is not None:
            conditions.append("m.command = %s")
            params.append(command.strip())
        if tenant_id is not None:
            conditions.append("m.tenant_id = %s")
            params.append(tenant_id.strip())
        if operator_id is not None:
            conditions.append("m.operator_id = %s")
            params.append(operator_id.strip())
        if status is not None:
            conditions.append("COALESCE(r.status, m.status) = %s")
            params.append(status.strip())

        where = (" AND ".join(conditions)) if conditions else "TRUE"
        count_sql = f"""
            SELECT count(*) FROM adapter_task_meta m
            LEFT JOIN adapter_results r ON m.task_id = r.task_id
            WHERE {where}
        """
        data_sql = f"""
            SELECT m.task_id, m.command, m.tenant_id, m.operator_id, m.session_key,
                   COALESCE(r.status, m.status) as status, m.decision,
                   m.owner_api_key_hash, m.created_at, m.updated_at,
                   m.started_at, m.finished_at,
                   r.result
            FROM adapter_task_meta m
            LEFT JOIN adapter_results r ON m.task_id = r.task_id
            WHERE {where}
            ORDER BY m.created_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """

        with self._conn() as conn:
            total_row = conn.execute(count_sql, params).fetchone()
            total = total_row[0] if total_row else 0
            rows = conn.execute(data_sql, params + [limit, offset]).fetchall()

        items = []
        for row in rows:
            item: Dict[str, Any] = {
                "task_id": row[0], "command": row[1], "tenant_id": row[2],
                "operator_id": row[3], "session_key": row[4], "status": row[5],
                "decision": row[6], "owner_api_key_hash": row[7],
            }
            for i, key in enumerate(["created_at", "updated_at", "started_at", "finished_at"], 8):
                val = row[i]
                item[key] = val.isoformat() if isinstance(val, datetime) else val
            result_data = row[12]
            if isinstance(result_data, dict):
                item["decision"] = result_data.get("decision", item.get("decision"))
                item["summary"] = str(result_data.get("summary", ""))[:180]
            items.append(item)

        return {"total": total, "limit": limit, "offset": offset, "items": items}

    # ── Events ──

    def save_event(self, task_id: str, event: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adapter_events (task_id, event_type, data, timestamp)
                   VALUES (%s, %s, %s::jsonb, %s)""",
                (
                    task_id,
                    event.get("type", "unknown"),
                    json.dumps(event.get("data", {}), ensure_ascii=False),
                    event.get("timestamp", datetime.now(timezone.utc).isoformat()),
                ),
            )
            conn.commit()

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT task_id, event_type, data, timestamp
                   FROM adapter_events WHERE task_id = %s ORDER BY id""",
                (task_id,),
            ).fetchall()
        events = []
        for row in rows:
            ev: Dict[str, Any] = {
                "task_id": row[0],
                "type": row[1],
                "data": row[2] if isinstance(row[2], dict) else json.loads(row[2]),
            }
            ts = row[3]
            ev["timestamp"] = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            events.append(ev)
        return events

    def delete_events(self, task_id: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM adapter_events WHERE task_id = %s", (task_id,)
            )
            conn.commit()
            return cur.rowcount

    # ── History logs ──

    def save_history(self, record: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO adapter_history_logs (action, task_id, payload, timestamp)
                   VALUES (%s, %s, %s::jsonb, %s)""",
                (
                    record.get("action", ""),
                    record.get("task_id"),
                    json.dumps(record.get("payload", {}), ensure_ascii=False),
                    record.get("timestamp", datetime.now(timezone.utc).isoformat()),
                ),
            )
            conn.commit()

    def list_history(
        self, *, task_id: Optional[str] = None, limit: int = 200
    ) -> List[Dict[str, Any]]:
        if task_id is not None:
            sql = """SELECT action, task_id, payload, timestamp
                     FROM adapter_history_logs WHERE task_id = %s
                     ORDER BY id DESC LIMIT %s"""
            params = (task_id, limit)
        else:
            sql = """SELECT action, task_id, payload, timestamp
                     FROM adapter_history_logs ORDER BY id DESC LIMIT %s"""
            params = (limit,)

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        result = []
        for row in reversed(rows):
            entry: Dict[str, Any] = {
                "action": row[0],
                "task_id": row[1],
                "payload": row[2] if isinstance(row[2], dict) else json.loads(row[2]),
            }
            ts = row[3]
            entry["timestamp"] = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            result.append(entry)
        return result

    # ── Cascade delete ──

    def delete_task(self, task_id: str) -> Dict[str, bool]:
        with self._conn() as conn:
            r_events = conn.execute(
                "DELETE FROM adapter_events WHERE task_id = %s", (task_id,)
            ).rowcount
            r_result = conn.execute(
                "DELETE FROM adapter_results WHERE task_id = %s", (task_id,)
            ).rowcount
            r_meta = conn.execute(
                "DELETE FROM adapter_task_meta WHERE task_id = %s", (task_id,)
            ).rowcount
            r_task = conn.execute(
                "DELETE FROM adapter_tasks WHERE task_id = %s", (task_id,)
            ).rowcount
            conn.commit()
        return {
            "removed_task": r_task > 0,
            "removed_result": r_result > 0,
            "removed_meta": r_meta > 0,
            "removed_events": r_events,
        }

    # ── Lifecycle ──

    def close(self) -> None:
        try:
            self._pool.close()
        except Exception:
            pass
