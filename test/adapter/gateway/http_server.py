"""FastAPI HTTP server for adapter plane.

This module is intentionally thin: route registration + request/response wiring.
Validation, access policy, and feature adaptation live in dedicated sub-layers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.api_server import (
    archive_logs,
    bootstrap_on_import,
    delete_history,
    get_compliance_feedback,
    get_result,
    list_history,
    list_logs,
    queue_runtime,
    stream_events,
    submit_task,
)
from .access_control import (
    CALLER_OPERATOR_HEADER,
    CALLER_TENANT_HEADER,
    endpoint_access_guard,
    task_access_guard,
)
from .feature_service import check_task_feature_match, submit_feature_command
from .http_access import HTTP_ACCESS
from .response_mapper import status_for_generic, status_for_query, status_for_submit
from ..sdk.access import SDK_ACCESS


def create_app():
    """Build FastAPI app lazily so module import does not require FastAPI."""
    bootstrap_on_import()

    try:
        from fastapi import Body, FastAPI, Header, Query
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI server requires `fastapi` and `uvicorn` to be installed.") from exc

    app = FastAPI(
        title="Audit Adapter API",
        version="0.4.0",
        description="HTTP wrapper for adapter task submission and retrieval.",
    )

    @app.get("/health")
    async def health(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)) -> Dict[str, str]:
        guard = endpoint_access_guard("health", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)
        return {"status": "ok"}

    @app.post("/api/{feature}")
    async def post_api_feature(
        feature: str,
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("feature_submit", api_key=api_key, feature=feature)
        if guard is not None:
            return JSONResponse(status_code=status_for_submit(guard), content=guard)
        response = submit_feature_command(
            feature,
            payload,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        return JSONResponse(status_code=status_for_submit(response), content=response)

    @app.post("/api/{feature}/{instruction}")
    async def post_api_feature_instruction(
        feature: str,
        instruction: str,
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("feature_submit", api_key=api_key, feature=feature, instruction=instruction)
        if guard is not None:
            return JSONResponse(status_code=status_for_submit(guard), content=guard)
        response = submit_feature_command(
            feature,
            payload,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
            instruction=instruction,
        )
        return JSONResponse(status_code=status_for_submit(response), content=response)

    @app.get("/api/task/{task_id}")
    async def get_api_task(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("task_query", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = get_result(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/api/task/{task_id}/events")
    async def get_api_task_events(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("task_events", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = stream_events(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/api/task/{task_id}/compliance")
    async def get_api_task_compliance(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("task_compliance", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/api/history")
    async def get_api_history(
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        command: Optional[str] = Query(default=None),
        tenant_id: Optional[str] = Query(default=None),
        operator_id: Optional[str] = Query(default=None),
        status: Optional[str] = Query(default=None),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = endpoint_access_guard("history_list", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = list_history(
            limit=limit,
            offset=offset,
            command=command,
            tenant_id=tenant_id,
            operator_id=operator_id,
            status=status,
        )
        return JSONResponse(status_code=status_for_generic(response), content=response)

    @app.delete("/api/history/{task_id}")
    async def delete_api_history(
        task_id: str,
        purge_events: bool = Query(default=True),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = endpoint_access_guard("history_delete", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = delete_history(task_id, purge_events=purge_events)
        return JSONResponse(status_code=status_for_generic(response), content=response)

    @app.get("/api/logs")
    async def get_api_logs(
        task_id: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=2000),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = endpoint_access_guard("logs_list", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = list_logs(task_id=task_id, limit=limit)
        return JSONResponse(status_code=status_for_generic(response), content=response)

    @app.post("/api/logs/archive")
    async def post_api_logs_archive(
        force: bool = Query(default=False),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = endpoint_access_guard("logs_archive", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = archive_logs(force=force)
        return JSONResponse(status_code=status_for_generic(response), content=response)

    @app.get("/api/runtime/queue")
    async def get_api_runtime_queue(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)):
        guard = endpoint_access_guard("runtime_queue", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = queue_runtime()
        return JSONResponse(status_code=status_for_generic(response), content=response)

    @app.get("/api/runtime/exposure")
    async def get_api_runtime_exposure(api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header)):
        guard = endpoint_access_guard("runtime_exposure", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_generic(guard), content=guard)

        response = {
            "status": "ok",
            "mapping": HTTP_ACCESS.command_by_feature(),
            "config": {
                "http": HTTP_ACCESS.redacted(),
                "sdk": SDK_ACCESS.redacted(),
            },
        }
        return JSONResponse(status_code=200, content=response)

    @app.get("/api/{feature}/{task_id}")
    async def get_api_feature_task(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("feature_query", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response, status_code = check_task_feature_match(feature, task_id)
        return JSONResponse(status_code=status_code, content=response)

    @app.get("/api/{feature}/{task_id}/events")
    async def get_api_feature_task_events(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("feature_events", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        check, status_code = check_task_feature_match(feature, task_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=check)

        response = stream_events(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/api/{feature}/{task_id}/compliance")
    async def get_api_feature_task_compliance(
        feature: str,
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("feature_compliance", api_key=api_key, feature=feature, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        check, status_code = check_task_feature_match(feature, task_id)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=check)

        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    # Legacy endpoints kept for compatibility but disabled by default.
    @app.post("/task")
    async def post_task(
        payload: Dict[str, Any] = Body(...),
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
    ):
        guard = endpoint_access_guard("legacy_task_submit", api_key=api_key)
        if guard is not None:
            return JSONResponse(status_code=status_for_submit(guard), content=guard)

        response = submit_task(payload, owner_api_key=api_key)
        return JSONResponse(status_code=status_for_submit(response), content=response)

    @app.get("/task/{task_id}")
    async def get_task(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("legacy_task_query", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = get_result(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/task/{task_id}/events")
    async def get_task_events(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("legacy_task_events", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = stream_events(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    @app.get("/task/{task_id}/compliance")
    async def get_task_compliance(
        task_id: str,
        api_key: Optional[str] = Header(default=None, alias=HTTP_ACCESS.auth_header),
        caller_tenant_id: Optional[str] = Header(default=None, alias=CALLER_TENANT_HEADER),
        caller_operator_id: Optional[str] = Header(default=None, alias=CALLER_OPERATOR_HEADER),
    ):
        guard = endpoint_access_guard("legacy_task_compliance", api_key=api_key, task_id=task_id)
        if guard is not None:
            return JSONResponse(status_code=status_for_query(guard), content=guard)

        owner_guard = task_access_guard(
            task_id=task_id,
            api_key=api_key,
            caller_tenant_id=caller_tenant_id,
            caller_operator_id=caller_operator_id,
        )
        if owner_guard is not None:
            return JSONResponse(status_code=status_for_query(owner_guard), content=owner_guard)

        response = get_compliance_feedback(task_id)
        return JSONResponse(status_code=status_for_query(response), content=response)

    return app


try:
    app = create_app()
except RuntimeError:  # pragma: no cover
    app = None


if __name__ == "__main__":  # pragma: no cover
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("Run server requires `uvicorn` to be installed.") from exc

    uvicorn.run(create_app(), host="0.0.0.0", port=8000, reload=False)
