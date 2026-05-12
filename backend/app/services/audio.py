from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChannelRoute, GenerationTask, new_id
from app.schemas import AudioTaskCreate
from app.services.channel_router import ChannelTransport, RouteNotFoundError
from app.services.generation import GenerationService
from app.services.generation_surface import namespace_request_key, normalize_generation_surface, surface_clause, surface_from_request_key
from app.services.model_configs import ModelConfigService
from app.services.wallet import InsufficientBalanceError, WalletNotFoundError
from app.tasks.generation import enqueue_generation_task, process_generation_task_once


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
        resolved = ModelConfigService(self.session).resolve_generation_target(
            tenant_id=tenant_id,
            target_type=payload.target_type,
            target_key=payload.target_id,
            fallback_route_key=payload.route_key,
        )
        route = self._audio_route(tenant_id=tenant_id, route_key=resolved.route_key)
        request_key = namespace_request_key(payload.surface, payload.request_key or f"audio:{new_id()}")
        generation = GenerationService(self.session)
        options = {
            **(payload.options or {}),
            **({"source_url": payload.source_url} if payload.source_url else {}),
            **({"voice": payload.voice_key} if payload.voice_key else {}),
        }
        task = generation.create_task(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type=payload.task_type,
            prompt=payload.prompt,
            route_key=route.route_key,
            estimated_cost=resolved.effective_point_cost,
            request_key=request_key,
            options=options,
        )
        if task.status == "PENDING":
            queued = enqueue_generation_task(tenant_id=tenant_id, task_id=task.id)
            if queued is False:
                try:
                    process_generation_task_once(session=self.session, tenant_id=tenant_id, task_id=task.id)
                except Exception:
                    pass
        return self._task_payload(task)

    def list_tasks(self, *, tenant_id: str, user_id: str = DEMO_AUDIO_USER_ID, surface: str = "portal", limit: int = 20) -> dict:
        normalized_surface = normalize_generation_surface(surface)
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
                    surface_clause(GenerationTask.request_key, normalized_surface),
                )
                .order_by(GenerationTask.created_at.desc())
                .limit(limit)
            )
        )
        return {"surface": normalized_surface, "tasks": [self._task_payload(task) for task in tasks]}

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
            "surface": surface_from_request_key(task.request_key),
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


__all__ = [
    "AUDIO_CHANNEL_TYPE",
    "DEMO_AUDIO_USER_ID",
    "AudioProviderError",
    "AudioService",
    "InsufficientBalanceError",
    "RouteNotFoundError",
    "WalletNotFoundError",
]
