from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ChannelRoute, GenerationTask, Tenant, User, Wallet


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


def test_video_generation_creates_pending_task_and_reserves_wallet_points(session):
    wallet = seed_video_runtime(session)
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
                request_key="video-old",
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
                request_key="video-new",
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
                id="task-other-tenant",
                tenant_id="tenant-b",
                user_id="tenant-b-user",
                request_key="video-other",
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

    response = client.get("/api/v1/video/workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-a"
    assert payload["user_id"] == "demo-user"
    assert payload["wallet"] == {"balance": wallet.balance, "frozen_balance": wallet.frozen_balance}
    assert payload["route"] == {"route_key": "video_text_to_video", "unit_cost": 200}
    assert [task["id"] for task in payload["tasks"]] == ["task-new", "task-old"]
    assert payload["tasks"][0]["provider_task_id"] == "provider-new"


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
