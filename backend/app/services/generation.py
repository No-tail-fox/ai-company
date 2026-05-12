from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, ChannelRoute, GenerationTask, utcnow
from app.services.channel_router import RouteNotFoundError
from app.services.wallet import WalletService


class GenerationTaskNotFoundError(Exception):
    pass


class GenerationService:
    def __init__(self, session: Session):
        self.session = session

    def create_task(
        self,
        *,
        tenant_id: str,
        user_id: str,
        task_type: str,
        prompt: str,
        route_key: str,
        estimated_cost: int,
        request_key: str,
        options: dict | None = None,
    ) -> GenerationTask:
        existing = self.session.scalar(
            select(GenerationTask).where(
                GenerationTask.tenant_id == tenant_id,
                GenerationTask.request_key == request_key,
            )
        )
        if existing:
            return existing

        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == route_key,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise RouteNotFoundError(f"route {route_key} was not found or is disabled")

        reservation_key = f"generation:{request_key}"
        reservation = WalletService(self.session).reserve_funds(
            tenant_id=tenant_id,
            user_id=user_id,
            amount=estimated_cost,
            reason=f"{task_type} generation reserved",
            request_key=reservation_key,
            source_type="GENERATION",
            source_ref=request_key,
        )
        task = GenerationTask(
            tenant_id=tenant_id,
            user_id=user_id,
            request_key=request_key,
            task_type=task_type,
            route_key=route_key,
            prompt=prompt,
            status="PENDING",
            reservation_key=reservation.request_key,
            estimated_cost=estimated_cost,
            actual_cost=None,
            options_json=options or {},
        )
        self.session.add(task)
        self.session.commit()
        return task

    def mark_processing(self, *, tenant_id: str, task_id: str, provider_task_id: str | None = None) -> GenerationTask:
        task = self._get_task(tenant_id, task_id)
        if task.status not in {"SUCCESS", "FAILED"}:
            task.status = "PROCESSING"
            task.provider_task_id = provider_task_id
            task.started_at = task.started_at or utcnow()
            self.session.commit()
        return task

    def complete_task(
        self,
        *,
        tenant_id: str,
        task_id: str,
        status: str,
        actual_cost: int,
        result_url: str | None = None,
        error_message: str | None = None,
    ) -> GenerationTask:
        task = self._get_task(tenant_id, task_id)
        if task.status in {"SUCCESS", "FAILED"}:
            return task

        charged_amount = actual_cost if status == "SUCCESS" else 0
        WalletService(self.session).finalize_reservation(
            tenant_id=tenant_id,
            user_id=task.user_id,
            request_key=task.reservation_key,
            estimated_amount=task.estimated_cost,
            actual_amount=charged_amount,
            reason=f"{task.task_type} generation settled",
        )

        task.status = status
        task.actual_cost = charged_amount
        task.result_url = result_url
        task.error_message = error_message
        task.completed_at = utcnow()

        if status == "SUCCESS" and result_url:
            existing_asset = self.session.scalar(
                select(Asset).where(
                    Asset.tenant_id == tenant_id,
                    Asset.generation_task_id == task.id,
                    Asset.deleted.is_(False),
                )
            )
            if existing_asset is None:
                self.session.add(
                    Asset(
                        tenant_id=tenant_id,
                        user_id=task.user_id,
                        generation_task_id=task.id,
                        asset_type=task.task_type,
                        title=task.prompt[:80],
                        url=result_url,
                        storage_key=result_url,
                        prompt=task.prompt,
                        public=False,
                    )
                )
        self.session.commit()
        return task

    def _get_task(self, tenant_id: str, task_id: str) -> GenerationTask:
        task = self.session.scalar(
            select(GenerationTask).where(
                GenerationTask.tenant_id == tenant_id,
                GenerationTask.id == task_id,
            )
        )
        if task is None:
            raise GenerationTaskNotFoundError(f"generation task {task_id} does not exist")
        return task
