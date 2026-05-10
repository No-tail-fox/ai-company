from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ApiChannel, Asset, ChannelRoute, ChatMessage, ChatSession, ModelConfig, User, new_id, utcnow
from app.schemas import ChatExportCreate, ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate
from app.services.channel_router import ChannelRouter, ChannelTransport, ChannelRoutingError, NoHealthyChannelError
from app.settings import get_settings


DEMO_CHAT_USER_ID = "demo-user"
DEFAULT_CHAT_MODEL_KEY = "general_text_default"
TEXT_CHANNEL_TYPE = "TEXT"


class ChatValidationError(ValueError):
    pass


class ChatNotFoundError(ValueError):
    pass


class ChatProviderError(RuntimeError):
    pass


class ChatService:
    def __init__(self, session: Session, transport: ChannelTransport):
        self.session = session
        self.transport = transport

    def get_workbench(
        self,
        *,
        tenant_id: str,
        user_id: str = DEMO_CHAT_USER_ID,
        session_id: str | None = None,
    ) -> dict:
        self._user(tenant_id=tenant_id, user_id=user_id)
        sessions = self._sessions(tenant_id=tenant_id, user_id=user_id)
        active = None
        if session_id:
            active = self._session(tenant_id=tenant_id, session_id=session_id, user_id=user_id)
        elif sessions:
            active = sessions[0]

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "sessions": [self._session_summary_payload(session) for session in sessions],
            "active_session": self._active_session_payload(active) if active is not None else None,
            "models": self._models(tenant_id=tenant_id),
        }

    def create_session(self, *, tenant_id: str, payload: ChatSessionCreate) -> dict:
        user_id = payload.user_id or DEMO_CHAT_USER_ID
        self._user(tenant_id=tenant_id, user_id=user_id)
        model_key = payload.model_key or DEFAULT_CHAT_MODEL_KEY
        if model_key:
            self._text_model(tenant_id=tenant_id, model_key=model_key, require_enabled_channel=False)
        chat = ChatSession(
            tenant_id=tenant_id,
            user_id=user_id,
            title=payload.title.strip(),
            preset_role=payload.preset_role.strip() or "assistant",
            model_key=model_key,
        )
        self.session.add(chat)
        self.session.commit()
        return self._active_session_payload(chat)

    def update_session(self, *, tenant_id: str, session_id: str, payload: ChatSessionUpdate) -> dict:
        chat = self._session(tenant_id=tenant_id, session_id=session_id)
        values = payload.model_dump(exclude_unset=True)
        if "model_key" in values and values["model_key"]:
            self._text_model(tenant_id=tenant_id, model_key=values["model_key"], require_enabled_channel=False)
        for key, value in values.items():
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            setattr(chat, key, value)
        chat.updated_at = utcnow()
        self.session.commit()
        return self._active_session_payload(chat)

    def get_session(self, *, tenant_id: str, session_id: str) -> dict:
        return self._active_session_payload(self._session(tenant_id=tenant_id, session_id=session_id))

    def send_message(self, *, tenant_id: str, session_id: str, payload: ChatMessageCreate) -> dict:
        content = payload.content.strip()
        if not content:
            raise ChatValidationError("message content is required")

        chat = self._session(tenant_id=tenant_id, session_id=session_id)
        model_key = (payload.model_key or chat.model_key or DEFAULT_CHAT_MODEL_KEY).strip()
        self._text_model(tenant_id=tenant_id, model_key=model_key, require_enabled_channel=True)
        sequence = self._next_sequence(session_id=session_id)
        user_message = ChatMessage(
            tenant_id=tenant_id,
            session_id=chat.id,
            role="user",
            content=content,
            sequence=sequence,
        )
        self.session.add(user_message)
        self.session.flush()

        if not chat.title.strip():
            chat.title = self._auto_title(content)
        chat.model_key = model_key
        chat.updated_at = utcnow()

        conversation = [
            {"role": message.role, "content": message.content}
            for message in self._messages(session_id=chat.id)
        ]
        provider_payload = {
            "session_id": chat.id,
            "preset_role": chat.preset_role,
            "messages": conversation,
        }
        try:
            result = ChannelRouter(self.session, self.transport).dispatch(
                tenant_id=tenant_id,
                route_key=model_key,
                payload=provider_payload,
            )
        except NoHealthyChannelError as exc:
            raise ChatProviderError(str(exc)) from exc
        except ChannelRoutingError as exc:
            raise ChatValidationError(str(exc)) from exc

        reply_content = self._reply_content(result.raw_payload)
        assistant_message = ChatMessage(
            tenant_id=tenant_id,
            session_id=chat.id,
            role="assistant",
            content=reply_content,
            sequence=sequence + 1,
        )
        chat.updated_at = utcnow()
        self.session.add(assistant_message)
        self.session.commit()
        return {
            "session": self._active_session_payload(chat),
            "messages_created": [
                self._message_payload(user_message),
                self._message_payload(assistant_message),
            ],
        }

    def export_session(self, *, tenant_id: str, session_id: str, payload: ChatExportCreate) -> dict:
        if payload.format.lower() != "markdown":
            raise ChatValidationError("only markdown export is supported")
        chat = self._session(tenant_id=tenant_id, session_id=session_id)
        messages = self._messages(session_id=chat.id)
        if not messages:
            raise ChatValidationError("session has no messages to export")

        file_name = f"{self._safe_file_stem(chat.title or chat.id)}.md"
        storage_key = f"exports/{tenant_id}/{chat.id}-{new_id()}.md"
        target = Path(get_settings().storage_dir) / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        content = self._markdown_content(chat, messages)
        target.write_text(content, encoding="utf-8")

        asset = Asset(
            tenant_id=tenant_id,
            user_id=chat.user_id,
            asset_type="MARKDOWN",
            title=file_name,
            url=f"/storage/{storage_key}",
            storage_key=storage_key,
            prompt=chat.title,
            public=False,
        )
        self.session.add(asset)
        self.session.flush()

        export_payload = {
            "id": asset.id,
            "url": asset.url,
            "storage_key": asset.storage_key,
            "file_name": file_name,
            "size": target.stat().st_size,
        }
        sequence = self._next_sequence(session_id=chat.id)
        message = ChatMessage(
            tenant_id=tenant_id,
            session_id=chat.id,
            role="assistant",
            content=f"Markdown export created: {file_name}",
            sequence=sequence,
        )
        chat.updated_at = utcnow()
        self.session.add(message)
        self.session.commit()
        return {
            "asset": export_payload,
            "message": {
                **self._message_payload(message),
                "export": export_payload,
            },
        }

    def _user(self, *, tenant_id: str, user_id: str) -> User:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.id == user_id,
                User.status == "ACTIVE",
            )
        )
        if user is None:
            raise ChatValidationError(f"user {user_id} was not found")
        return user

    def _session(self, *, tenant_id: str, session_id: str, user_id: str | None = None) -> ChatSession:
        filters = [
            ChatSession.tenant_id == tenant_id,
            ChatSession.id == session_id,
            ChatSession.status != "DELETED",
        ]
        if user_id is not None:
            filters.append(ChatSession.user_id == user_id)
        chat = self.session.scalar(select(ChatSession).where(*filters))
        if chat is None:
            raise ChatNotFoundError(f"chat session {session_id} was not found")
        return chat

    def _sessions(self, *, tenant_id: str, user_id: str, limit: int = 80) -> list[ChatSession]:
        return list(
            self.session.scalars(
                select(ChatSession)
                .where(
                    ChatSession.tenant_id == tenant_id,
                    ChatSession.user_id == user_id,
                    ChatSession.status == "ACTIVE",
                )
                .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
                .limit(limit)
            )
        )

    def _messages(self, *, session_id: str) -> list[ChatMessage]:
        return list(
            self.session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.sequence.asc(), ChatMessage.created_at.asc())
            )
        )

    def _models(self, *, tenant_id: str) -> list[dict]:
        rows = self.session.execute(
            select(ModelConfig, ApiChannel)
            .join(ApiChannel, ApiChannel.id == ModelConfig.channel_id)
            .where(
                ModelConfig.tenant_id == tenant_id,
                ModelConfig.capability == TEXT_CHANNEL_TYPE,
                ModelConfig.enabled.is_(True),
                ApiChannel.enabled.is_(True),
                ApiChannel.channel_type == TEXT_CHANNEL_TYPE,
            )
            .order_by(ModelConfig.default_point_cost.asc(), ModelConfig.created_at.asc())
        )
        return [
            {
                "id": model.id,
                "model_key": model.model_key,
                "display_name": model.display_name,
                "provider_model": model.provider_model,
                "default_point_cost": model.default_point_cost,
                "channel_key": channel.channel_key,
            }
            for model, channel in rows
        ]

    def _text_model(self, *, tenant_id: str, model_key: str, require_enabled_channel: bool) -> ModelConfig:
        model = self.session.scalar(
            select(ModelConfig).where(
                ModelConfig.tenant_id == tenant_id,
                ModelConfig.model_key == model_key,
                ModelConfig.capability == TEXT_CHANNEL_TYPE,
                ModelConfig.enabled.is_(True),
            )
        )
        if model is None:
            raise ChatValidationError(f"text model {model_key} is not configured or is disabled")

        channel = self.session.get(ApiChannel, model.channel_id)
        if channel is None or channel.channel_type != TEXT_CHANNEL_TYPE:
            raise ChatValidationError(f"text model {model_key} has no TEXT provider channel")
        if require_enabled_channel and not channel.enabled:
            raise ChatValidationError(f"text provider channel {channel.channel_key} is disabled")

        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == model.model_key,
                ChannelRoute.channel_type == TEXT_CHANNEL_TYPE,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise ChatValidationError(f"text route {model_key} was not found or is disabled")
        return model

    def _next_sequence(self, *, session_id: str) -> int:
        current = self.session.scalar(
            select(func.max(ChatMessage.sequence)).where(ChatMessage.session_id == session_id)
        )
        return int(current or 0) + 1

    def _active_session_payload(self, chat: ChatSession) -> dict:
        return {
            **self._session_summary_payload(chat),
            "preset_role": chat.preset_role,
            "model_key": chat.model_key,
            "status": chat.status,
            "messages": [self._message_payload(message) for message in self._messages(session_id=chat.id)],
        }

    def _session_summary_payload(self, chat: ChatSession) -> dict:
        messages = self._messages(session_id=chat.id)
        preview = ""
        if messages:
            preview = messages[-1].content[:120]
        return {
            "id": chat.id,
            "tenant_id": chat.tenant_id,
            "user_id": chat.user_id,
            "title": chat.title,
            "preview": preview,
            "preset_role": chat.preset_role,
            "model_key": chat.model_key,
            "status": chat.status,
            "message_count": len(messages),
            "created_at": chat.created_at.isoformat() if chat.created_at else None,
            "updated_at": chat.updated_at.isoformat() if chat.updated_at else None,
        }

    @staticmethod
    def _message_payload(message: ChatMessage) -> dict:
        return {
            "id": message.id,
            "tenant_id": message.tenant_id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "sequence": message.sequence,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }

    @staticmethod
    def _reply_content(raw: dict[str, Any]) -> str:
        for key in ("content", "message", "text", "reply"):
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
        raise ChatProviderError("text provider returned no message content")

    @staticmethod
    def _auto_title(content: str) -> str:
        normalized = " ".join(content.split())
        return normalized[:30]

    @staticmethod
    def _safe_file_stem(value: str) -> str:
        cleaned = "".join("-" if char in '\\/:*?"<>|' else char for char in value).strip(" .")
        return (cleaned or "chat-export")[:80]

    @staticmethod
    def _markdown_content(chat: ChatSession, messages: list[ChatMessage]) -> str:
        lines = [f"# {chat.title or chat.id}", ""]
        for message in messages:
            lines.extend([f"## {message.role}", message.content, ""])
        return "\n".join(lines).rstrip() + "\n"
