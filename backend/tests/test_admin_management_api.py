from datetime import timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import MembershipPlan, Tenant, User, UserMembership, Wallet, utcnow
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def login_admin(client: TestClient, tenant_id: str, phone: str = "13900000000", password: str = "admin123456") -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": phone, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str, tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {token}"}


def test_admin_dashboard_manages_users_memberships_and_points(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    user = User(
        id="user-a",
        tenant_id=tenant.id,
        phone="13800000000",
        display_name="演示用户",
        role="USER",
        status="ACTIVE",
    )
    wallet = Wallet(id="wallet-a", tenant_id=tenant.id, user_id=user.id, balance=1200, frozen_balance=50)
    plan = MembershipPlan(
        id="plan-a",
        tenant_id=tenant.id,
        plan_key="vip_monthly",
        name="VIP 月卡",
        price_cents=1990,
        duration_days=31,
        entitlements=["assistant.vip", "template.vip"],
        enabled=True,
        sort_order=10,
    )
    membership = UserMembership(
        id="membership-a",
        tenant_id=tenant.id,
        user_id=user.id,
        plan_id=plan.id,
        status="ACTIVE",
        started_at=utcnow() - timedelta(days=1),
        expires_at=utcnow() + timedelta(days=30),
    )
    session.add_all([tenant, admin, user, wallet, plan, membership])
    session.commit()

    client = make_client(session)
    token = login_admin(client, tenant.id)
    headers = auth_headers(token, tenant.id)

    overview = client.get("/api/v1/admin/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["users"]["total"] == 2
    assert overview.json()["wallets"]["total_balance"] == 1200
    assert overview.json()["membership_plans"]["total"] == 1

    users = client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    user_rows = users.json()["users"]
    assert any(row["display_name"] == "管理员" for row in user_rows)
    assert any(row["membership_plan_name"] == "VIP 月卡" for row in user_rows)

    created = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "phone": "13700000000",
            "display_name": "新成员",
            "role": "OPERATOR",
            "status": "ACTIVE",
            "password": "operator123",
        },
    )
    assert created.status_code == 201
    created_user_id = created.json()["id"]

    updated = client.put(
        f"/api/v1/admin/users/{created_user_id}",
        headers=headers,
        json={"display_name": "运营成员", "role": "CONTENT_EDITOR", "status": "ACTIVE"},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "CONTENT_EDITOR"

    adjusted = client.post(
        f"/api/v1/admin/wallets/{user.id}/adjust",
        headers=headers,
        json={"amount": 300, "reason": "手工充值"},
    )
    assert adjusted.status_code == 200
    assert adjusted.json()["balance"] == 1500

    transactions = client.get("/api/v1/admin/wallet-transactions?user_id=user-a", headers=headers)
    assert transactions.status_code == 200
    assert transactions.json()["transactions"][0]["amount"] == 300

    plan_created = client.post(
        "/api/v1/admin/membership-plans",
        headers=headers,
        json={
            "plan_key": "vip_quarterly",
            "name": "VIP 季卡",
            "price_cents": 4990,
            "duration_days": 90,
            "entitlements": ["assistant.vip", "template.vip", "community.vip"],
            "enabled": True,
            "sort_order": 20,
        },
    )
    assert plan_created.status_code == 201
    new_plan_id = plan_created.json()["id"]

    membership_grant = client.post(
        "/api/v1/admin/user-memberships",
        headers=headers,
        json={
            "user_id": created_user_id,
            "plan_id": new_plan_id,
            "duration_days": 60,
        },
    )
    assert membership_grant.status_code == 201
    assert membership_grant.json()["plan"]["name"] == "VIP 季卡"

    memberships = client.get(f"/api/v1/admin/user-memberships?user_id={created_user_id}", headers=headers)
    assert memberships.status_code == 200
    assert memberships.json()["memberships"][0]["plan"]["name"] == "VIP 季卡"

    logs = client.get("/api/v1/admin/audit-logs?limit=5", headers=headers)
    assert logs.status_code == 200
    assert logs.json()["logs"]


def test_admin_read_only_role_blocks_mutations(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    read_only = User(
        id="reader-a",
        tenant_id=tenant.id,
        phone="13600000000",
        display_name="只读账号",
        role="READ_ONLY",
        password_hash=hash_password("reader123"),
    )
    session.add_all([tenant, read_only])
    session.commit()

    client = make_client(session)
    token = login_admin(client, tenant.id, phone="13600000000", password="reader123")
    headers = auth_headers(token, tenant.id)

    response = client.post(
        "/api/v1/admin/users",
        headers=headers,
        json={
            "phone": "13500000000",
            "display_name": "不该通过",
            "role": "USER",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 403
