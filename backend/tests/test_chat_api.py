from pathlib import Path

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ApiChannel, Asset, ChannelRoute, ChatMessage, ChatSession, ModelConfig, Tenant, User
from app.settings import get_settings


class FakeChatTransport:
    def __init__(self):
        self.calls = []

    def send(self, channel, route, payload):
        self.calls.append({"channel": channel, "route": route, "payload": payload})
        prompt = payload["messages"][-1]["content"]
        return {
            "provider_task_id": "provider-chat-1",
            "content": f"模型回复：{prompt}",
        }


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session, transport=None) -> TestClient:
    app = create_app(chat_transport=transport or FakeChatTransport())
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_chat_runtime(session, *, tenant_id="tenant-a", user_id="demo-user"):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant A")
    user = User(id=user_id, tenant_id=tenant_id, phone="13800000000", display_name="Demo User", role="USER")
    channel = ApiChannel(
        id="channel-text",
        tenant_id=tenant_id,
        channel_key="text-provider",
        display_name="TEXT Provider",
        base_url="https://text.example.com/generate",
        api_key="secret",
        channel_type="TEXT",
        enabled=True,
    )
    route = ChannelRoute(
        id="route-general-text",
        tenant_id=tenant_id,
        route_key="general_text_default",
        display_name="通用文本模型",
        backend_model="provider-text-model",
        channel_type="TEXT",
        unit_cost=10,
        enabled=True,
    )
    model = ModelConfig(
        id="model-general-text",
        tenant_id=tenant_id,
        model_key="general_text_default",
        display_name="GPT-4.1",
        capability="TEXT",
        channel_id=channel.id,
        provider_model="provider-text-model",
        default_point_cost=10,
        enabled=True,
    )
    session.add_all([tenant, user, channel, route, model])
    session.commit()
    return user


def test_chat_workbench_returns_sessions_models_and_active_messages(session):
    seed_chat_runtime(session)
    chat = ChatSession(
        id="chat-a",
        tenant_id="tenant-a",
        user_id="demo-user",
        title="项目周报整理",
        preset_role="通用助手",
        model_key="general_text_default",
    )
    session.add(chat)
    session.add_all(
        [
            ChatMessage(id="msg-a1", tenant_id="tenant-a", session_id=chat.id, role="user", content="整理项目进展", sequence=1),
            ChatMessage(id="msg-a2", tenant_id="tenant-a", session_id=chat.id, role="assistant", content="已整理完成", sequence=2),
        ]
    )
    session.commit()
    client = make_client(session)

    response = client.get("/api/v1/chat/workbench?session_id=chat-a", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-a"
    assert payload["active_session"]["id"] == "chat-a"
    assert payload["active_session"]["messages"][0]["content"] == "整理项目进展"
    assert payload["sessions"][0]["title"] == "项目周报整理"
    assert payload["models"][0]["model_key"] == "general_text_default"
    assert payload["models"][0]["display_name"] == "GPT-4.1"


def test_chat_message_calls_text_model_and_persists_messages(session):
    seed_chat_runtime(session)
    transport = FakeChatTransport()
    client = make_client(session, transport)

    create_response = client.post(
        "/api/v1/chat/sessions",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"title": "", "model_key": "general_text_default", "preset_role": "通用助手"},
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"content": "请整理本周项目进展", "model_key": "general_text_default"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert [message["role"] for message in payload["messages_created"]] == ["user", "assistant"]
    assert payload["messages_created"][1]["content"] == "模型回复：请整理本周项目进展"
    assert transport.calls[0]["route"].route_key == "general_text_default"
    assert transport.calls[0]["payload"]["messages"][-1] == {"role": "user", "content": "请整理本周项目进展"}
    saved_session = session.get(ChatSession, session_id)
    assert saved_session.title == "请整理本周项目进展"
    assert session.query(ChatMessage).filter_by(session_id=session_id).count() == 2


def test_chat_export_creates_markdown_asset_and_file_card_message(session, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    get_settings.cache_clear()
    seed_chat_runtime(session)
    chat = ChatSession(
        id="chat-export",
        tenant_id="tenant-a",
        user_id="demo-user",
        title="项目周报",
        preset_role="通用助手",
        model_key="general_text_default",
    )
    session.add(chat)
    session.add_all(
        [
            ChatMessage(id="msg-e1", tenant_id="tenant-a", session_id=chat.id, role="user", content="整理项目进展", sequence=1),
            ChatMessage(id="msg-e2", tenant_id="tenant-a", session_id=chat.id, role="assistant", content="项目进展如下", sequence=2),
        ]
    )
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/chat/sessions/chat-export/export",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"format": "markdown"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["asset"]["file_name"].endswith(".md")
    saved = Path(tmp_path) / payload["asset"]["storage_key"]
    assert saved.exists()
    assert "## user" in saved.read_text(encoding="utf-8")
    asset = session.query(Asset).filter_by(id=payload["asset"]["id"]).one()
    assert asset.asset_type == "MARKDOWN"
    assert payload["message"]["role"] == "assistant"
    assert payload["message"]["export"]["url"] == asset.url
