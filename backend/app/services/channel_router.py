from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiChannel, ChannelRoute, new_id, utcnow
from app.settings import get_settings


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
        channel_filters = [
            ApiChannel.tenant_id == tenant_id,
            ApiChannel.channel_type == route.channel_type,
            ApiChannel.enabled.is_(True),
        ]
        route_metadata = route.metadata_json if isinstance(route.metadata_json, dict) else {}
        target_channel_id = str(route_metadata.get("channel_id") or "").strip()
        target_channel_key = str(route_metadata.get("channel_key") or "").strip()
        if target_channel_id:
            channel_filters.append(ApiChannel.id == target_channel_id)
        elif target_channel_key:
            channel_filters.append(ApiChannel.channel_key == target_channel_key)

        channels = list(
            self.session.scalars(
                select(ApiChannel)
                .where(*channel_filters)
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
        if (getattr(channel, "adapter_type", "") or "custom_http") == "openai_compatible":
            return self._send_openai_compatible(channel, route, payload)
        return self._send_custom_http(channel, route, payload)

    def _send_custom_http(self, channel: ApiChannel, route: ChannelRoute, payload: dict[str, Any]) -> dict[str, Any]:
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

    def _send_openai_compatible(self, channel: ApiChannel, route: ChannelRoute, payload: dict[str, Any]) -> dict[str, Any]:
        base_url = channel.base_url.rstrip("/")
        headers = {"Authorization": f"Bearer {channel.api_key}"}
        with httpx.Client(timeout=channel.timeout_seconds) as client:
            if route.channel_type == "TEXT":
                return self._openai_text(client=client, base_url=base_url, headers=headers, route=route, payload=payload)
            if route.channel_type == "IMAGE":
                return self._openai_image(client=client, base_url=base_url, headers=headers, route=route, payload=payload)
            if route.channel_type == "AUDIO":
                return self._openai_audio(client=client, base_url=base_url, headers=headers, route=route, payload=payload)
            if route.channel_type == "VIDEO":
                return self._openai_video(client=client, base_url=base_url, headers=headers, route=route, payload=payload)
        raise ChannelRoutingError(f"unsupported openai compatible channel type {route.channel_type}")

    def _openai_text(
        self,
        *,
        client: httpx.Client,
        base_url: str,
        headers: dict[str, str],
        route: ChannelRoute,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": route.backend_model,
            "input": payload.get("messages") or payload.get("prompt") or "",
        }
        preset_role = payload.get("preset_role")
        if isinstance(preset_role, str) and preset_role.strip():
            body["instructions"] = preset_role.strip()
        body.update(self._clean_options(payload.get("options")))
        response = client.post(f"{base_url}/responses", json=body, headers=headers)
        response.raise_for_status()
        raw = response.json()
        return {**raw, "content": self._extract_text(raw)}

    def _openai_image(
        self,
        *,
        client: httpx.Client,
        base_url: str,
        headers: dict[str, str],
        route: ChannelRoute,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": route.backend_model,
            "prompt": payload.get("prompt", ""),
        }
        body.update(self._clean_options(payload.get("options"), allowed={"size", "quality", "n", "background", "moderation", "output_format"}))
        response = client.post(f"{base_url}/images/generations", json=body, headers=headers)
        response.raise_for_status()
        raw = response.json()
        return self._normalize_image_result(raw=raw, payload=payload)

    def _openai_audio(
        self,
        *,
        client: httpx.Client,
        base_url: str,
        headers: dict[str, str],
        route: ChannelRoute,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        task_type = str(payload.get("task_type", "")).upper()
        if task_type == "TRANSCRIPTION":
            body = {
                "model": route.backend_model,
                "input": payload.get("source_url") or payload.get("prompt", ""),
            }
            body.update(self._clean_options(payload.get("options")))
            response = client.post(f"{base_url}/audio/transcriptions", json=body, headers=headers)
            response.raise_for_status()
            raw = response.json()
            return {**raw, "result_url": raw.get("result_url") or raw.get("url"), "content": self._extract_text(raw)}

        options = self._clean_options(payload.get("options"), allowed={"voice", "speed", "response_format", "instructions"})
        body = {
            "model": route.backend_model,
            "input": payload.get("prompt", ""),
            "voice": options.pop("voice", payload.get("voice_key") or "alloy"),
            **options,
        }
        response = client.post(f"{base_url}/audio/speech", json=body, headers=headers)
        response.raise_for_status()
        return self._normalize_audio_result(response=response, payload=payload)

    def _openai_video(
        self,
        *,
        client: httpx.Client,
        base_url: str,
        headers: dict[str, str],
        route: ChannelRoute,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if payload.get("action") == "status" and payload.get("provider_task_id"):
            response = client.get(f"{base_url}/videos/{payload['provider_task_id']}", headers=headers)
            response.raise_for_status()
            raw = response.json()
            return self._normalize_async_result(raw)

        body = {
            "model": route.backend_model,
            "prompt": payload.get("prompt", ""),
        }
        body.update(self._clean_options(payload.get("options"), allowed={"size", "seconds", "duration", "response_format"}))
        response = client.post(f"{base_url}/videos", json=body, headers=headers)
        response.raise_for_status()
        raw = response.json()
        return self._normalize_async_result(raw)

    def _normalize_image_result(self, *, raw: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        item = self._first_data_item(raw)
        result_url = item.get("url") or raw.get("result_url") or raw.get("url")
        if result_url:
            return {**raw, "result_url": result_url}
        b64_json = item.get("b64_json") or raw.get("b64_json")
        if isinstance(b64_json, str) and b64_json:
            return {**raw, **self._save_base64_asset(payload=payload, b64_json=b64_json, extension=".png")}
        return raw

    def _normalize_audio_result(self, *, response: Any, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            raw = response.json()
        except Exception:  # noqa: BLE001 - binary speech responses are expected.
            raw = None
        if isinstance(raw, dict):
            result_url = raw.get("result_url") or raw.get("url")
            if result_url:
                return {**raw, "result_url": result_url}
            if isinstance(raw.get("b64_json"), str):
                return {**raw, **self._save_base64_asset(payload=payload, b64_json=raw["b64_json"], extension=".mp3")}
            return raw
        content = getattr(response, "content", b"")
        if content:
            return self._save_binary_asset(payload=payload, content=content, extension=".mp3")
        return {}

    def _normalize_async_result(self, raw: dict[str, Any]) -> dict[str, Any]:
        provider_task_id = raw.get("provider_task_id") or raw.get("id")
        status_value = raw.get("status")
        return {
            **raw,
            "provider_task_id": provider_task_id,
            "status": status_value.upper() if isinstance(status_value, str) else status_value,
            "result_url": raw.get("result_url") or raw.get("url") or raw.get("download_url"),
        }

    def _save_base64_asset(self, *, payload: dict[str, Any], b64_json: str, extension: str) -> dict[str, str]:
        return self._save_binary_asset(
            payload=payload,
            content=base64.b64decode(b64_json),
            extension=extension,
        )

    def _save_binary_asset(self, *, payload: dict[str, Any], content: bytes, extension: str) -> dict[str, str]:
        tenant_id = str(payload.get("tenant_id") or "default")
        task_id = str(payload.get("task_id") or new_id())
        storage_key = f"generated/{tenant_id}/{task_id}{extension}"
        target = Path(os.getenv("STORAGE_DIR") or get_settings().storage_dir) / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return {
            "result_url": f"/storage/{storage_key}",
            "storage_key": storage_key,
        }

    @staticmethod
    def _clean_options(value: Any, allowed: set[str] | None = None) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        cleaned = {str(key): option for key, option in value.items() if option not in (None, "")}
        if allowed is not None:
            cleaned = {key: option for key, option in cleaned.items() if key in allowed}
        return cleaned

    @staticmethod
    def _first_data_item(raw: dict[str, Any]) -> dict[str, Any]:
        data = raw.get("data")
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def _extract_text(raw: dict[str, Any]) -> str:
        for key in ("output_text", "content", "text", "message", "reply"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        choices = raw.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"].strip()
                if isinstance(first.get("text"), str):
                    return first["text"].strip()
        output = raw.get("output")
        if isinstance(output, list):
            parts: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if isinstance(content, list):
                    for content_item in content:
                        if isinstance(content_item, dict):
                            text = content_item.get("text")
                            if isinstance(text, str):
                                parts.append(text)
                elif isinstance(content, str):
                    parts.append(content)
            joined = "\n".join(part.strip() for part in parts if part.strip())
            if joined:
                return joined
        return ""
