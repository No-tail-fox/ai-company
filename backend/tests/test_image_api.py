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


def seed_image_runtime(session, *, tenant_id="tenant-a", user_id="demo-user", balance=1000):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant A")
    user = User(id=user_id, tenant_id=tenant_id, phone="13800000000", role="USER")
    wallet = Wallet(id=f"wallet-{tenant_id}", tenant_id=tenant_id, user_id=user_id, balance=balance, frozen_balance=0)
    route = ChannelRoute(
        id=f"route-image-{tenant_id}",
        tenant_id=tenant_id,
        route_key="image_text_to_image",
        display_name="一句话生成图片",
        backend_model="demo-image-renderer",
        channel_type="IMAGE",
        unit_cost=80,
        enabled=True,
    )
    session.add_all([tenant, user, wallet, route])
    session.commit()
    return wallet


def test_image_generation_creates_pending_task_and_reserves_wallet_points(session):
    wallet = seed_image_runtime(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成一张夏季新品推广海报", "request_key": "image-1"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["task_type"] == "IMAGE"
    assert payload["route_key"] == "image_text_to_image"
    assert payload["prompt"] == "生成一张夏季新品推广海报"
    assert payload["status"] == "PENDING"
    assert payload["estimated_cost"] == 80
    assert payload["surface"] == "portal"
    assert wallet.balance == 920
    assert wallet.frozen_balance == 80


def test_image_generation_supports_workbench_surface(session):
    wallet = seed_image_runtime(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "workbench image", "request_key": "image-wb", "surface": "workbench"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["surface"] == "workbench"
    task = session.query(GenerationTask).filter_by(id=payload["id"]).one()
    assert task.request_key.startswith("workbench:")
    assert wallet.balance == 920
    assert wallet.frozen_balance == 80


def test_image_generation_request_key_is_idempotent(session):
    wallet = seed_image_runtime(session)
    client = make_client(session)

    first = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成企业介绍配图", "request_key": "image-idempotent"},
    )
    second = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成企业介绍配图", "request_key": "image-idempotent"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert wallet.balance == 920
    assert wallet.frozen_balance == 80


def test_image_workbench_returns_wallet_route_and_recent_image_tasks(session):
    wallet = seed_image_runtime(session, tenant_id="tenant-a")
    seed_image_runtime(session, tenant_id="tenant-b", user_id="tenant-b-user")
    now = datetime(2026, 5, 9, 9, 30)
    session.add_all(
        [
            GenerationTask(
                id="image-task-old",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="portal:image-old",
                task_type="IMAGE",
                route_key="image_text_to_image",
                prompt="旧图片任务",
                status="PENDING",
                reservation_key="reservation-old",
                estimated_cost=80,
                created_at=now - timedelta(hours=1),
            ),
            GenerationTask(
                id="image-task-new",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="workbench:image-new",
                task_type="IMAGE",
                route_key="image_text_to_image",
                prompt="新图片任务",
                status="PROCESSING",
                reservation_key="reservation-new",
                estimated_cost=80,
                provider_task_id="provider-new",
                created_at=now,
            ),
            GenerationTask(
                id="image-task-legacy",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="image-legacy",
                task_type="IMAGE",
                route_key="image_text_to_image",
                prompt="旧图像任务",
                status="SUCCESS",
                reservation_key="reservation-legacy",
                estimated_cost=80,
                actual_cost=80,
                result_url="https://cdn.example.com/legacy.png",
                created_at=now - timedelta(hours=2),
            ),
            GenerationTask(
                id="video-task",
                tenant_id="tenant-a",
                user_id="demo-user",
                request_key="workbench:video-task",
                task_type="VIDEO",
                route_key="video_text_to_video",
                prompt="视频任务不应出现",
                status="PENDING",
                reservation_key="reservation-video",
                estimated_cost=200,
                created_at=now + timedelta(hours=1),
            ),
            GenerationTask(
                id="image-task-other-tenant",
                tenant_id="tenant-b",
                user_id="tenant-b-user",
                request_key="workbench:image-other",
                task_type="IMAGE",
                route_key="image_text_to_image",
                prompt="其它租户",
                status="PENDING",
                reservation_key="reservation-other",
                estimated_cost=80,
                created_at=now + timedelta(hours=2),
            ),
        ]
    )
    session.commit()
    client = make_client(session)

    workbench_response = client.get(
        "/api/v1/image/workbench?surface=workbench",
        headers={"X-Tenant-ID": "tenant-a"},
    )
    portal_response = client.get("/api/v1/image/workbench", headers={"X-Tenant-ID": "tenant-a"})

    assert workbench_response.status_code == 200
    workbench_payload = workbench_response.json()
    assert workbench_payload["surface"] == "workbench"
    assert [task["id"] for task in workbench_payload["tasks"]] == ["image-task-new"]
    assert workbench_payload["tasks"][0]["surface"] == "workbench"
    assert workbench_payload["tasks"][0]["provider_task_id"] == "provider-new"

    assert portal_response.status_code == 200
    portal_payload = portal_response.json()
    assert portal_payload["surface"] == "portal"
    assert [task["id"] for task in portal_payload["tasks"]] == ["image-task-old", "image-task-legacy"]
    assert portal_payload["tasks"][0]["surface"] == "portal"
    assert portal_payload["wallet"] == {"balance": wallet.balance, "frozen_balance": wallet.frozen_balance}
    assert portal_payload["route"] == {"route_key": "image_text_to_image", "unit_cost": 80}


def test_image_generation_rejects_empty_prompt(session):
    seed_image_runtime(session)
    client = make_client(session)

    response = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "  "},
    )

    assert response.status_code == 400
    assert "prompt" in response.json()["detail"]


def test_image_generation_rejects_insufficient_wallet_balance(session):
    seed_image_runtime(session, balance=20)
    client = make_client(session)

    response = client.post(
        "/api/v1/image/generations",
        headers={"X-Tenant-ID": "tenant-a"},
        json={"prompt": "生成会员宣传海报"},
    )

    assert response.status_code == 400
    assert "balance" in response.json()["detail"]
