from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChannelRoute, GenerationTask, new_id
from app.schemas import AudioTaskCreate
from app.services.channel_router import ChannelRouter, ChannelTransport, NoHealthyChannelError, RouteNotFoundError
from app.services.generation import GenerationService
from app.services.wallet import InsufficientBalanceError, WalletNotFoundError


DEMO_AUDIO_USER_ID = "demo-user"
AUDIO_CHANNEL_TYPE = "AUDIO"


class AudioTaskError(Exception):
    pass


class AudioProviderError(AudioTaskError):
    pass


class AudioService:
    def __init__(self, session: Session, transport: ChannelTransport):
        self.session = session
        self.transport = transport

    def create_task(self, *, tenant_id: str, payload: AudioTaskCreate, user_id: str = DEMO_AUDIO_USER_ID) -> dict:
        route = self._audio_route(tenant_id=tenant_id, route_key=payload.route_key)
        request_key = f"audio:{new_id()}"
        generation = GenerationService(self.session)
        task = generation.create_task(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type=payload.task_type,
            prompt=payload.prompt,
            route_key=route.route_key,
            estimated_cost=route.unit_cost,
            request_key=request_key,
        )
        try:
            dispatch = ChannelRouter(self.session, self.transport).dispatch(
                tenant_id=tenant_id,
                route_key=route.route_key,
                payload=_provider_payload(payload, task.id),
            )
            generation.mark_processing(tenant_id=tenant_id, task_id=task.id, provider_task_id=dispatch.provider_task_id)
            if not dispatch.result_url:
                generation.complete_task(
                    tenant_id=tenant_id,
                    task_id=task.id,
                    status="FAILED",
                    actual_cost=0,
                    error_message="audio provider did not return result_url",
                )
                raise AudioProviderError("audio provider did not return result_url")
            completed = generation.complete_task(
                tenant_id=tenant_id,
                task_id=task.id,
                status="SUCCESS",
                actual_cost=route.unit_cost,
                result_url=dispatch.result_url,
            )
            return self._task_payload(completed)
        except (NoHealthyChannelError, RouteNotFoundError) as exc:
            generation.complete_task(
                tenant_id=tenant_id,
                task_id=task.id,
                status="FAILED",
                actual_cost=0,
                error_message=str(exc),
            )
            raise AudioProviderError(str(exc)) from exc

    def list_tasks(self, *, tenant_id: str, user_id: str = DEMO_AUDIO_USER_ID, limit: int = 20) -> dict:
        route_keys = [
            route_key
            for route_key in self.session.scalars(
                select(ChannelRoute.route_key).where(
                    ChannelRoute.tenant_id == tenant_id,
                    ChannelRoute.channel_type == AUDIO_CHANNEL_TYPE,
                )
            )
        ]
        if not route_keys:
            return {"tasks": []}
        tasks = list(
            self.session.scalars(
                select(GenerationTask)
                .where(
                    GenerationTask.tenant_id == tenant_id,
                    GenerationTask.user_id == user_id,
                    GenerationTask.route_key.in_(route_keys),
                )
                .order_by(GenerationTask.created_at.desc())
                .limit(limit)
            )
        )
        return {"tasks": [self._task_payload(task) for task in tasks]}

    def _audio_route(self, *, tenant_id: str, route_key: str) -> ChannelRoute:
        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == route_key,
                ChannelRoute.channel_type == AUDIO_CHANNEL_TYPE,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise RouteNotFoundError(f"audio route {route_key} was not found or is disabled")
        return route

    @staticmethod
    def _task_payload(task: GenerationTask) -> dict:
        return {
            "id": task.id,
            "tenant_id": task.tenant_id,
            "user_id": task.user_id,
            "task_type": task.task_type,
            "route_key": task.route_key,
            "prompt": task.prompt,
            "status": task.status,
            "estimated_cost": task.estimated_cost,
            "actual_cost": task.actual_cost,
            "provider_task_id": task.provider_task_id,
            "result_url": task.result_url,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }


def _provider_payload(payload: AudioTaskCreate, task_id: str) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "task_id": task_id,
            "task_type": payload.task_type,
            "prompt": payload.prompt,
            "source_url": payload.source_url,
            "voice_key": payload.voice_key,
        }.items()
        if value
    }


__all__ = [
    "AUDIO_CHANNEL_TYPE",
    "DEMO_AUDIO_USER_ID",
    "AudioProviderError",
    "AudioService",
    "InsufficientBalanceError",
    "RouteNotFoundError",
    "WalletNotFoundError",
]
