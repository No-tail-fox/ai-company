from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiChannel, ChannelRoute, utcnow


class ChannelRoutingError(Exception):
    pass


class RouteNotFoundError(ChannelRoutingError):
    pass


class NoHealthyChannelError(ChannelRoutingError):
    pass


class ChannelTransport(Protocol):
    def send(self, channel: ApiChannel, route: ChannelRoute, payload: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class DispatchResult:
    channel_key: str
    provider_task_id: str | None
    result_url: str | None
    raw_payload: dict[str, Any]


class ChannelRouter:
    def __init__(self, session: Session, transport: ChannelTransport):
        self.session = session
        self.transport = transport

    def dispatch(self, *, tenant_id: str, route_key: str, payload: dict[str, Any]) -> DispatchResult:
        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == route_key,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise RouteNotFoundError(f"route {route_key} was not found or is disabled")

        now = utcnow()
        channels = list(
            self.session.scalars(
                select(ApiChannel)
                .where(
                    ApiChannel.tenant_id == tenant_id,
                    ApiChannel.channel_type == route.channel_type,
                    ApiChannel.enabled.is_(True),
                )
                .order_by(ApiChannel.priority.asc(), ApiChannel.created_at.asc())
            )
        )
        channels = [
            channel
            for channel in channels
            if channel.unhealthy_until is None or channel.unhealthy_until <= now
        ]
        if not channels:
            raise NoHealthyChannelError(f"no enabled channel exists for route {route_key}")

        last_error: Exception | None = None
        for channel in channels:
            try:
                raw = self.transport.send(channel, route, payload)
            except Exception as exc:  # noqa: BLE001 - channel errors must trigger fallback.
                last_error = exc
                channel.error_count += 1
                channel.health_status = "DEGRADED"
                channel.unhealthy_until = now + timedelta(seconds=max(channel.timeout_seconds, 1))
                self.session.flush()
                continue

            channel.error_count = 0
            channel.health_status = "HEALTHY"
            channel.unhealthy_until = None
            self.session.commit()
            return DispatchResult(
                channel_key=channel.channel_key,
                provider_task_id=raw.get("provider_task_id"),
                result_url=raw.get("result_url"),
                raw_payload=raw,
            )

        self.session.commit()
        raise NoHealthyChannelError(f"all channels failed for route {route_key}: {last_error}")


class HttpChannelTransport:
    def send(self, channel: ApiChannel, route: ChannelRoute, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {channel.api_key}",
            "X-Channel-Key": channel.channel_key,
            "X-Route-Key": route.route_key,
        }
        provider_payload = {
            **payload,
            "model": route.backend_model,
            "route_key": route.route_key,
        }
        with httpx.Client(timeout=channel.timeout_seconds) as client:
            response = client.post(channel.base_url, json=provider_payload, headers=headers)
            response.raise_for_status()
            raw = response.json()
        if isinstance(raw, dict) and isinstance(raw.get("data"), dict):
            return {**raw, **raw["data"]}
        return raw if isinstance(raw, dict) else {"raw": raw}
