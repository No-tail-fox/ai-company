from datetime import timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import MembershipPlan, Tenant, User, UserMembership, Wallet, WalletTransaction, utcnow
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_redemption_context(session):
    tenant = Tenant(id="tenant-redemption", slug="tenant-redemption", name="Tenant Redemption")
    admin = User(
        id="admin-redemption",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="Admin",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    user = User(
        id="user-redemption",
        tenant_id=tenant.id,
        phone="13800000002",
        display_name="Redeemer",
        role="USER",
        password_hash=hash_password("user123456"),
    )
    wallet = Wallet(id="wallet-redemption", tenant_id=tenant.id, user_id=user.id, balance=100, frozen_balance=0)
    plan = MembershipPlan(
        id="plan-redemption",
        tenant_id=tenant.id,
        plan_key="vip_monthly",
        name="VIP Monthly",
        price_cents=1990,
        duration_days=31,
        entitlements=["assistant.vip"],
        enabled=True,
    )
    session.add_all([tenant, admin, user, wallet, plan])
    session.commit()
    return tenant, user, wallet, plan


def login_admin(client: TestClient, tenant_id: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def login_user(client: TestClient, tenant_id: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13800000002", "password": "user123456", "verification_code": "123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_generates_code_and_user_redeems_points_and_membership(session):
    tenant, user, wallet, plan = seed_redemption_context(session)
    client = make_client(session)
    admin_headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_admin(client, tenant.id)}"}

    generated = client.post(
        "/api/v1/admin/redemption-batches",
        headers=admin_headers,
        json={
            "name": "May VIP bundle",
            "quantity": 2,
            "points": 500,
            "membership_plan_id": plan.id,
            "membership_days": 30,
        },
    )

    assert generated.status_code == 201
    payload = generated.json()
    assert payload["batch"]["name"] == "May VIP bundle"
    assert payload["batch"]["quantity"] == 2
    assert len(payload["codes"]) == 2
    plain_code = payload["codes"][0]["code"]
    assert plain_code

    listed = client.get("/api/v1/admin/redemption-batches", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()["batches"][0]["generated_count"] == 2

    user_headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_user(client, tenant.id)}"}
    redeemed = client.post(
        "/api/v1/redemptions/redeem",
        headers=user_headers,
        json={"code": plain_code.lower()},
    )

    assert redeemed.status_code == 200
    redemption = redeemed.json()
    assert redemption["status"] == "REDEEMED"
    assert redemption["points_granted"] == 500
    assert redemption["wallet"]["balance"] == 600
    assert redemption["membership"]["active"] is True
    assert redemption["membership"]["plan"]["id"] == plan.id
    assert wallet.balance == 600
    assert session.query(WalletTransaction).filter_by(user_id=user.id, type="RECHARGE").count() == 1
    assert session.query(UserMembership).filter_by(user_id=user.id, plan_id=plan.id, status="ACTIVE").count() == 1

    second_redeem = client.post("/api/v1/redemptions/redeem", headers=user_headers, json={"code": plain_code})
    assert second_redeem.status_code == 400


def test_redemption_rejects_disabled_and_expired_codes(session):
    tenant, _, _, plan = seed_redemption_context(session)
    client = make_client(session)
    admin_headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_admin(client, tenant.id)}"}
    user_headers = {"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {login_user(client, tenant.id)}"}

    generated = client.post(
        "/api/v1/admin/redemption-batches",
        headers=admin_headers,
        json={
            "name": "Expired batch",
            "quantity": 2,
            "points": 100,
            "membership_plan_id": plan.id,
            "expires_at": (utcnow() - timedelta(days=1)).isoformat(),
        },
    )
    assert generated.status_code == 201
    first_code = generated.json()["codes"][0]
    second_code = generated.json()["codes"][1]

    disabled = client.delete(f"/api/v1/admin/redemption-codes/{first_code['id']}", headers=admin_headers)
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "DISABLED"

    disabled_redeem = client.post("/api/v1/redemptions/redeem", headers=user_headers, json={"code": first_code["code"]})
    assert disabled_redeem.status_code == 400

    expired_redeem = client.post("/api/v1/redemptions/redeem", headers=user_headers, json={"code": second_code["code"]})
    assert expired_redeem.status_code == 400
    assert "expired" in expired_redeem.json()["detail"]
