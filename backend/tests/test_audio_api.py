from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ApiChannel, Asset, ChannelRoute, GenerationTask, Tenant, User, Wallet


def override_session(session):
    def _override():
        yield session

    return _override


class FakeAudioTransport:
    def __init__(self, *, result_url: str | None = "https://cdn.example.com/audio.mp3"):
        self.result_url = result_url
        self.calls = []

    def send(self, channel, route, payload):
        self.calls.append({"channel": channel.channel_key, "route": route.route_key, "payload": payload})
        return {"provider_task_id": "provider-audio-1", "result_url": self.result_url}


def make_client(session, transport=None) -> TestClient:
    app = create_app(audio_transport=transport)
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_audio_runtime(session, *, tenant_id="tenant-a", user_id="demo-user"):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant A")
    user = User(id=user_id, tenant_id=tenant_id, phone="13800000000", role="USER")
    wallet = Wallet(id=f"wallet-{tenant_id}", tenant_id=tenant_id, user_id=user_id, balance=1000, frozen_balance=0)
    route = ChannelRoute(
        id=f"route-{tenant_id}",
        tenant_id=tenant_id,
        route_key="audio_tts",
        display_name="文本转语音",
        backend_model="demo-tts",
        channel_type="AUDIO",
        unit_cost=120,
        enabled=True,
    )
    channel = ApiChannel(
        id=f"channel-{tenant_id}",
        tenant_id=tenant_id,
        channel_key="demo-audio",
        display_name="Demo Audio",
        base_url="https://audio.example.com/generate",
        api_key="secret",
        channel_type="AUDIO",
        priority=1,
        enabled=True,
    )
    session.add_all([tenant, user, wallet, route, channel])
    session.commit()
    return wallet


def test_audio_upload_accepts_audio_files(session, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    session.add(Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"))
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/audio/uploads",
        headers={"X-Tenant-ID": "tenant-a"},
        files={"file": ("voice.mp3", b"audio-content", "audio/mpeg")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["url"].startswith("/storage/uploads/tenant-a/")
    assert payload["storage_key"].endswith(".mp3")
    assert (tmp_path / payload["storage_key"]).exists()


def test_audio_upload_rejects_non_audio_files(session, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    session.add(Tenant(id="tenant-a", slug="tenant-a", name="Tenant A"))
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/audio/uploads",
        headers={"X-Tenant-ID": "tenant-a"},
        files={"file": ("payload.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400


def test_audio_task_dispatches_sync_provider_and_creates_asset(session):
    wallet = seed_audio_runtime(session)
    transport = FakeAudioTransport()
    client = make_client(session, transport)

    response = client.post(
        "/api/v1/audio/tasks",
        headers={"X-Tenant-ID": "tenant-a"},
        json={
            "task_type": "TTS",
            "route_key": "audio_tts",
            "prompt": "欢迎使用 AI 音频工作台",
            "voice_key": "voice-warm-female",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "SUCCESS"
    assert payload["result_url"] == "https://cdn.example.com/audio.mp3"
    assert payload["actual_cost"] == 120
    assert wallet.balance == 880
    assert wallet.frozen_balance == 0
    assert session.query(Asset).filter_by(asset_type="TTS").count() == 1
    assert transport.calls[0]["payload"]["voice_key"] == "voice-warm-female"


def test_audio_task_failure_releases_reserved_wallet_funds(session):
    wallet = seed_audio_runtime(session)
    transport = FakeAudioTransport(result_url=None)
    client = make_client(session, transport)

    response = client.post(
        "/api/v1/audio/tasks",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"task_type": "TTS", "route_key": "audio_tts", "prompt": "missing result"},
    )

    assert response.status_code == 502
    task = session.query(GenerationTask).filter_by(route_key="audio_tts").one()
    assert task.status == "FAILED"
    assert wallet.balance == 1000
    assert wallet.frozen_balance == 0


def test_audio_tasks_list_returns_demo_user_tasks_for_current_tenant(session):
    seed_audio_runtime(session, tenant_id="tenant-a")
    seed_audio_runtime(session, tenant_id="tenant-b", user_id="tenant-b-user")
    session.add(
        GenerationTask(
            id="task-a",
            tenant_id="tenant-a",
            user_id="demo-user",
            request_key="task-a",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant a",
            status="SUCCESS",
            reservation_key="reservation-a",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/a.mp3",
        )
    )
    session.add(
        GenerationTask(
            id="task-b",
            tenant_id="tenant-b",
            user_id="tenant-b-user",
            request_key="task-b",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant b",
            status="SUCCESS",
            reservation_key="reservation-b",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/b.mp3",
        )
    )
    session.commit()
    client = make_client(session)

    response = client.get("/api/v1/audio/tasks", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    payload = response.json()
    assert [task["id"] for task in payload["tasks"]] == ["task-a"]
    assert payload["tasks"][0]["result_url"] == "https://cdn.example.com/a.mp3"
