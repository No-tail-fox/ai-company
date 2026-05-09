from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChannelRoute, GenerationTask, User, Wallet, new_id
from app.schemas import ImageGenerationCreate
from app.services.channel_router import RouteNotFoundError
from app.services.generation import GenerationService
from app.services.wallet import InsufficientBalanceError, WalletNotFoundError


DEMO_IMAGE_USER_ID = "demo-user"
DEFAULT_IMAGE_ROUTE_KEY = "image_text_to_image"
IMAGE_CHANNEL_TYPE = "IMAGE"
IMAGE_TASK_TYPE = "IMAGE"


class ImageValidationError(ValueError):
    pass


class ImageUserNotFoundError(ValueError):
    pass


class ImageService:
    def __init__(self, session: Session):
        self.session = session

    def get_workbench(self, *, tenant_id: str, user_id: str = DEMO_IMAGE_USER_ID, limit: int = 20) -> dict:
        self._user(tenant_id=tenant_id, user_id=user_id)
        wallet = self._wallet(tenant_id=tenant_id, user_id=user_id)
        route = self._image_route(tenant_id=tenant_id, route_key=DEFAULT_IMAGE_ROUTE_KEY)
        tasks = list(
            self.session.scalars(
                select(GenerationTask)
                .where(
                    GenerationTask.tenant_id == tenant_id,
                    GenerationTask.user_id == user_id,
                    GenerationTask.task_type == IMAGE_TASK_TYPE,
                )
                .order_by(GenerationTask.created_at.desc())
                .limit(limit)
            )
        )
        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "wallet": {
                "balance": wallet.balance,
                "frozen_balance": wallet.frozen_balance,
            },
            "route": {
                "route_key": route.route_key,
                "unit_cost": route.unit_cost,
            },
            "tasks": [self._task_payload(task) for task in tasks],
        }

    def create_generation(self, *, tenant_id: str, payload: ImageGenerationCreate) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise ImageValidationError("prompt is required")

        user_id = payload.user_id or DEMO_IMAGE_USER_ID
        route_key = payload.route_key or DEFAULT_IMAGE_ROUTE_KEY
        self._user(tenant_id=tenant_id, user_id=user_id)
        self._wallet(tenant_id=tenant_id, user_id=user_id)
        route = self._image_route(tenant_id=tenant_id, route_key=route_key)
        request_key = payload.request_key or f"image:{new_id()}"

        task = GenerationService(self.session).create_task(
            tenant_id=tenant_id,
            user_id=user_id,
            task_type=IMAGE_TASK_TYPE,
            prompt=prompt,
            route_key=route.route_key,
            estimated_cost=route.unit_cost,
            request_key=request_key,
        )
        return self._task_payload(task)

    def _user(self, *, tenant_id: str, user_id: str) -> User:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.id == user_id,
                User.status == "ACTIVE",
            )
        )
        if user is None:
            raise ImageUserNotFoundError(f"user {user_id} was not found")
        return user

    def _wallet(self, *, tenant_id: str, user_id: str) -> Wallet:
        wallet = self.session.scalar(
            select(Wallet).where(
                Wallet.tenant_id == tenant_id,
                Wallet.user_id == user_id,
            )
        )
        if wallet is None:
            raise WalletNotFoundError(f"wallet for user {user_id} in tenant {tenant_id} was not found")
        return wallet

    def _image_route(self, *, tenant_id: str, route_key: str) -> ChannelRoute:
        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == route_key,
                ChannelRoute.channel_type == IMAGE_CHANNEL_TYPE,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise RouteNotFoundError(f"image route {route_key} was not found or is disabled")
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


__all__ = [
    "DEFAULT_IMAGE_ROUTE_KEY",
    "DEMO_IMAGE_USER_ID",
    "IMAGE_CHANNEL_TYPE",
    "IMAGE_TASK_TYPE",
    "ImageService",
    "ImageUserNotFoundError",
    "ImageValidationError",
    "InsufficientBalanceError",
    "RouteNotFoundError",
    "WalletNotFoundError",
]
