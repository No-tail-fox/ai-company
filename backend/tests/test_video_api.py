from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ChannelRoute, GenerationTask, Tenant, User, Wallet
from app.services import video as video_module


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_video_runtime(session, *, tenant_id="tenant-a", user_id="demo-user", balance=1000):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant A")
    user = User(id=user_id, tenant_id=tenant_id, phone="13800000000", role="USER")
    wallet = Wallet(id=f"wallet-{tenant_id}", tenant_id=tenant_id, user_id=user_id, balance=balance, frozen_balance=0)
    route = ChannelRoute(
        id=f"route-video-{tenant_id}",
        tenant_id=tenant_id,
        route_key="video_text_to_video",
        display_name="文案生成视频",
        backend_model="demo-video-renderer",
        channel_type="VIDEO",
        unit_cost=200,
        enabled=True,
    )
    session.add_all([tenant, user, wallet, route])
    session.commit()
    return wallet


def test_video_generation_creates_pending_task_reserves_wallet_points_and_enqueues_worker(session, monkeypatch):
    wallet = seed_video_runtime(session)
    enqueued = []
    monkeypatch.setattr(
        video_module,
        "enqueue_generation_task",
        lambda *, tenant_id, task_id: enqueued.append((tenant_id, task_id)),
        raising=False,
    )
    client = make_client(session)

    response = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成一条新品上市推广视频", "request_key": "video-1"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["task_type"] == "VIDEO"
    assert payload["route_key"] == "video_text_to_video"
    assert payload["prompt"] == "生成一条新品上市推广视频"
    assert payload["status"] == "PENDING"
    assert payload["estimated_cost"] == 200
    assert payload["surface"] == "portal"
    assert wallet.balance == 800
    assert wallet.frozen_balance == 200
    assert enqueued == [("tenant-a", payload["id"])]


def test_video_generation_supports_workbench_surface(session):
    wallet = seed_video_runtime(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "workbench video", "request_key": "video-wb", "surface": "workbench"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["surface"] == "workbench"
    task = session.query(GenerationTask).filter_by(id=payload["id"]).one()
    assert task.request_key.startswith("workbench:")
    assert wallet.balance == 800
    assert wallet.frozen_balance == 200


def test_video_generation_request_key_is_idempotent(session):
    wallet = seed_video_runtime(session)
    client = make_client(session)

    first = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成企业介绍视频", "request_key": "video-idempotent"},
    )
    second = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成企业介绍视频", "request_key": "video-idempotent"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert wallet.balance == 800
    assert wallet.frozen_balance == 200


def test_video_workbench_returns_wallet_route_and_recent_tasks_for_current_user(session):
    wallet = seed_video_runtime(session, tenant_id="tenant-a")
    seed_video_runtime(session, tenant_id="tenant-b", user_id="tenant-b-user")
    now = datetime(2026, 5, 9, 9, 30)
    session.add_all(
        [
            GenerationTask(
                id="task-old",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="portal:video-old",
                task_type="VIDEO",
                route_key="video_text_to_video",
                prompt="旧任务",
                status="PENDING",
                reservation_key="reservation-old",
                estimated_cost=200,
                created_at=now - timedelta(hours=1),
            ),
            GenerationTask(
                id="task-new",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="workbench:video-new",
                task_type="VIDEO",
                route_key="video_text_to_video",
                prompt="新任务",
                status="PROCESSING",
                reservation_key="reservation-new",
                estimated_cost=200,
                provider_task_id="provider-new",
                created_at=now,
            ),
            GenerationTask(
                id="task-legacy",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="video-legacy",
                task_type="VIDEO",
                route_key="video_text_to_video",
                prompt="legacy task",
                status="SUCCESS",
                reservation_key="reservation-legacy",
                estimated_cost=200,
                actual_cost=200,
                result_url="https://cdn.example.com/legacy.mp4",
                created_at=now - timedelta(hours=2),
            ),
            GenerationTask(
                id="task-other-tenant",
                tenant_id="tenant-b",
                user_id="tenant-b-user",
                request_key="workbench:video-other",
                task_type="VIDEO",
                route_key="video_text_to_video",
                prompt="其它租户",
                status="PENDING",
                reservation_key="reservation-other",
                estimated_cost=200,
                created_at=now + timedelta(hours=1),
            ),
        ]
    )
    session.commit()
    client = make_client(session)

    workbench_response = client.get(
        "/api/v1/video/workbench?surface=workbench",
        headers={"X-Tenant-ID": "tenant-a"},
    )
    portal_response = client.get("/api/v1/video/workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert workbench_response.status_code == 200
    workbench_payload = workbench_response.json()
    assert workbench_payload["surface"] == "workbench"
    assert [task["id"] for task in workbench_payload["tasks"]] == ["task-new"]
    assert workbench_payload["tasks"][0]["surface"] == "workbench"
    assert workbench_payload["tasks"][0]["provider_task_id"] == "provider-new"

    assert portal_response.status_code == 200
    portal_payload = portal_response.json()
    assert portal_payload["tenant_id"] == "tenant-a"
    assert portal_payload["user_id"] == "demo-user"
    assert portal_payload["surface"] == "portal"
    assert portal_payload["wallet"] == {"balance": wallet.balance, "frozen_balance": wallet.frozen_balance}
    assert portal_payload["route"] == {"route_key": "video_text_to_video", "unit_cost": 200}
    assert [task["id"] for task in portal_payload["tasks"]] == ["task-old", "task-legacy"]
    assert portal_payload["tasks"][0]["surface"] == "portal"


def test_video_generation_rejects_empty_prompt(session):
    seed_video_runtime(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "  "},
    )

    assert response.status_code == 400
    assert "prompt" in response.json()["detail"]


def test_video_generation_rejects_insufficient_wallet_balance(session):
    seed_video_runtime(session, balance=100)
    client = make_client(session)

    response = client.post(
        "/api/v1/video/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成会员宣传视频"},
    )

    assert response.status_code == 400
    assert "balance" in response.json()["detail"]
