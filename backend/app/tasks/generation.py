from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models import ChannelRoute, GenerationTask
from app.services.channel_router import ChannelRouter, ChannelTransport, HttpChannelTransport
from app.services.generation import GenerationService


TERMINAL_FAILURE_STATUSES = {"FAILED", "ERROR", "CANCELED", "CANCELLED"}
PROCESSING_STATUSES = {"PENDING", "PROCESSING", "RUNNING", "QUEUED"}
SUCCESS_STATUSES = {"SUCCESS", "SUCCEEDED", "COMPLETED", "DONE"}


def enqueue_generation_task(*, tenant_id: str, task_id: str) -> bool:
    try:
        process_generation_task.apply_async(
            kwargs={"tenant_id": tenant_id, "task_id": task_id},
            retry=False,
        )
    except Exception:
        return False
    return True


def process_generation_task_once(
    *,
    session: Session,
    tenant_id: str,
    task_id: str,
    transport: ChannelTransport | None = None,
) -> dict[str, Any]:
    generation = GenerationService(session)
    task = generation._get_task(tenant_id, task_id)
    if task.status in {"SUCCESS", "FAILED"}:
        return {"status": task.status, "task_id": task.id}

    route = _route_for_task(session=session, tenant_id=tenant_id, task=task)
    payload = _provider_payload(task=task, route=route)
    dispatch = ChannelRouter(session, transport or HttpChannelTransport()).dispatch(
        tenant_id=tenant_id,
        route_key=task.route_key,
        payload=payload,
    )
    raw = dispatch.raw_payload
    provider_status = _normalize_status(raw.get("status"))
    provider_task_id = dispatch.provider_task_id or task.provider_task_id

    if provider_status in TERMINAL_FAILURE_STATUSES:
        failed = generation.complete_task(
            tenant_id=tenant_id,
            task_id=task.id,
            status="FAILED",
            actual_cost=0,
            error_message=_error_message(raw),
        )
        return {"status": failed.status, "task_id": failed.id, "error_message": failed.error_message}

    if dispatch.result_url:
        completed = generation.complete_task(
            tenant_id=tenant_id,
            task_id=task.id,
            status="SUCCESS",
            actual_cost=task.estimated_cost,
            result_url=dispatch.result_url,
        )
        return {"status": completed.status, "task_id": completed.id, "result_url": completed.result_url}

    if provider_task_id and (provider_status in PROCESSING_STATUSES or provider_status is None):
        processing = generation.mark_processing(
            tenant_id=tenant_id,
            task_id=task.id,
            provider_task_id=provider_task_id,
        )
        return {"status": processing.status, "task_id": processing.id, "provider_task_id": processing.provider_task_id}

    if provider_status in SUCCESS_STATUSES:
        error_message = "generation provider reported success without result_url"
    else:
        error_message = _error_message(raw)
    failed = generation.complete_task(
        tenant_id=tenant_id,
        task_id=task.id,
        status="FAILED",
        actual_cost=0,
        error_message=error_message,
    )
    return {"status": failed.status, "task_id": failed.id, "error_message": failed.error_message}


@celery_app.task(bind=True, name="generation.process", max_retries=60)
def process_generation_task(self, *, tenant_id: str, task_id: str) -> dict[str, Any]:
    with SessionLocal() as session:
        result = process_generation_task_once(session=session, tenant_id=tenant_id, task_id=task_id)
    if result["status"] == "PROCESSING":
        raise self.retry(countdown=10)
    return result


def _route_for_task(*, session: Session, tenant_id: str, task: GenerationTask) -> ChannelRoute:
    route = session.scalar(
        select(ChannelRoute).where(
            ChannelRoute.tenant_id == tenant_id,
            ChannelRoute.route_key == task.route_key,
            ChannelRoute.enabled.is_(True),
        )
    )
    if route is None:
        raise ValueError(f"route {task.route_key} was not found or is disabled")
    return route


def _provider_payload(*, task: GenerationTask, route: ChannelRoute) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": "status" if task.provider_task_id else "create",
        "task_id": task.id,
        "task_type": task.task_type,
        "prompt": task.prompt,
        "model": route.backend_model,
        "route_key": route.route_key,
    }
    if task.provider_task_id:
        payload["provider_task_id"] = task.provider_task_id
    return payload


def _normalize_status(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().upper()


def _error_message(raw: dict[str, Any]) -> str:
    for key in ("error_message", "message", "error"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "generation provider did not return a usable result"


__all__ = ["enqueue_generation_task", "process_generation_task_once", "process_generation_task"]
