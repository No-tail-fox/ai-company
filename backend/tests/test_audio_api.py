from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ApiChannel, Asset, ChannelRoute, GenerationTask, Tenant, User, Wallet
from app.services import audio as audio_module


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


def test_audio_task_enqueues_pending_task_and_reserves_wallet_points(session, monkeypatch):
    wallet = seed_audio_runtime(session)
    transport = FakeAudioTransport()
    enqueued = []
    monkeypatch.setattr(
        audio_module,
        "enqueue_generation_task",
        lambda *, tenant_id, task_id: enqueued.append((tenant_id, task_id)),
        raising=False,
    )
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
    assert payload["status"] == "PENDING"
    assert payload["result_url"] is None
    assert payload["actual_cost"] is None
    assert payload["surface"] == "portal"
    assert wallet.balance == 880
    assert wallet.frozen_balance == 120
    assert session.query(Asset).filter_by(asset_type="TTS").count() == 0
    assert transport.calls == []
    assert enqueued == [("tenant-a", payload["id"])]


def test_audio_task_create_supports_workbench_surface(session):
    seed_audio_runtime(session)
    transport = FakeAudioTransport()
    client = make_client(session, transport)

    response = client.post(
        "/api/v1/audio/tasks",
        headers={"X-Tenant-ID": "tenant-a"},
        json={
            "task_type": "TTS",
            "route_key": "audio_tts",
            "prompt": "workbench audio",
            "voice_key": "voice-warm-female",
            "request_key": "audio-wb",
            "surface": "workbench",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["surface"] == "workbench"
    task = session.query(GenerationTask).filter_by(id=payload["id"]).one()
    assert task.request_key.startswith("workbench:")


def test_audio_task_provider_failure_is_deferred_to_worker(session, monkeypatch):
    wallet = seed_audio_runtime(session)
    transport = FakeAudioTransport(result_url=None)
    enqueued = []
    monkeypatch.setattr(
        audio_module,
        "enqueue_generation_task",
        lambda *, tenant_id, task_id: enqueued.append((tenant_id, task_id)),
        raising=False,
    )
    client = make_client(session, transport)

    response = client.post(
        "/api/v1/audio/tasks",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"task_type": "TTS", "route_key": "audio_tts", "prompt": "missing result"},
    )

    assert response.status_code == 201
    payload = response.json()
    task = session.query(GenerationTask).filter_by(route_key="audio_tts").one()
    assert task.status == "PENDING"
    assert payload["status"] == "PENDING"
    assert wallet.balance == 880
    assert wallet.frozen_balance == 120
    assert transport.calls == []
    assert enqueued == [("tenant-a", payload["id"])]


def test_audio_tasks_list_returns_demo_user_tasks_for_current_tenant(session):
    seed_audio_runtime(session, tenant_id="tenant-a")
    seed_audio_runtime(session, tenant_id="tenant-b", user_id="tenant-b-user")
    now = datetime(2026, 5, 9, 9, 30)
    session.add(
        GenerationTask(
            id="task-a",
            tenant_id="tenant-a",
            user_id="demo-user",
            request_key="portal:task-a",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant a",
            status="SUCCESS",
            reservation_key="reservation-a",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/a.mp3",
            created_at=now,
        )
    )
    session.add(
        GenerationTask(
            id="task-workbench",
            tenant_id="tenant-a",
            user_id="demo-user",
            request_key="workbench:task-workbench",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant a workbench",
            status="SUCCESS",
            reservation_key="reservation-workbench",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/workbench.mp3",
            created_at=now - timedelta(hours=1),
        )
    )
    session.add(
        GenerationTask(
            id="task-legacy",
            tenant_id="tenant-a",
            user_id="demo-user",
            request_key="task-legacy",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant a legacy",
            status="SUCCESS",
            reservation_key="reservation-legacy",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/legacy.mp3",
            created_at=now - timedelta(hours=2),
        )
    )
    session.add(
        GenerationTask(
            id="task-b",
            tenant_id="tenant-b",
            user_id="tenant-b-user",
            request_key="workbench:task-b",
            task_type="TTS",
            route_key="audio_tts",
            prompt="tenant b",
            status="SUCCESS",
            reservation_key="reservation-b",
            estimated_cost=120,
            actual_cost=120,
            result_url="https://cdn.example.com/b.mp3",
            created_at=now - timedelta(hours=3),
        )
    )
    session.commit()
    client = make_client(session)

    portal_response = client.get("/api/v1/audio/tasks", headers={"X-Tenant-ID": "tenant-a"})
    workbench_response = client.get("/api/v1/audio/tasks?surface=workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert portal_response.status_code == 200
    portal_payload = portal_response.json()
    assert portal_payload["surface"] == "portal"
    assert [task["id"] for task in portal_payload["tasks"]] == ["task-a", "task-legacy"]
    assert portal_payload["tasks"][0]["result_url"] == "https://cdn.example.com/a.mp3"

    assert workbench_response.status_code == 200
    workbench_payload = workbench_response.json()
    assert workbench_payload["surface"] == "workbench"
    assert [task["id"] for task in workbench_payload["tasks"]] == ["task-workbench"]
    assert workbench_payload["tasks"][0]["surface"] == "workbench"
