from datetime import timedelta

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import MembershipPlan, PaymentOrder, Tenant, User, UserMembership, Wallet, utcnow


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_account(session, *, tenant_id="tenant-a", user_id="demo-user", balance=120000):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant A")
    user = User(
        id=user_id,
        tenant_id=tenant.id,
        phone="13800000000",
        display_name="演示用户",
        role="USER",
    )
    wallet = Wallet(id="wallet-demo", tenant_id=tenant.id, user_id=user.id, balance=balance, frozen_balance=80)
    session.add_all([tenant, user, wallet])
    return tenant, user, wallet


def test_account_summary_returns_user_wallet_and_membership_status(session):
    tenant, user, wallet = seed_account(session)
    plan = MembershipPlan(
        id="plan-vip",
        tenant_id=tenant.id,
        plan_key="vip_monthly",
        name="VIP 月卡",
        price_cents=1990,
        duration_days=31,
        entitlements=["assistant.vip", "template.vip"],
        enabled=True,
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
    session.add_all([plan, membership])
    session.commit()
    client = make_client(session)

    response = client.get("/api/v1/account/summary?user_id=demo-user", headers={"X-Tenant-ID": tenant.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["display_name"] == "演示用户"
    assert payload["user"]["phone"] == "13800000000"
    assert payload["wallet"] == {"balance": wallet.balance, "frozen_balance": 80, "currency": "POINT"}
    assert payload["membership"]["active"] is True
    assert payload["membership"]["plan"]["name"] == "VIP 月卡"
    assert payload["membership"]["entitlements"] == ["assistant.vip", "template.vip"]


def test_account_profile_update_persists_display_name(session):
    tenant, user, _ = seed_account(session)
    session.commit()
    client = make_client(session)

    response = client.patch(
        "/api/v1/account/profile",
        headers={"X-Tenant-ID": tenant.id},
        json={"user_id": user.id, "display_name": "新昵称"},
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "新昵称"
    assert user.display_name == "新昵称"


def test_recharge_order_creates_pending_order_without_changing_wallet_balance(session):
    tenant, user, wallet = seed_account(session, balance=600)
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/payments/recharge-orders",
        headers={"X-Tenant-ID": tenant.id},
        json={"user_id": user.id, "package_key": "points_5000"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "PENDING"
    assert payload["package_key"] == "points_5000"
    assert payload["points"] == 5000
    assert payload["amount_cents"] == 4900
    assert "支付渠道" in payload["message"]
    assert wallet.balance == 600
    order = session.query(PaymentOrder).filter_by(tenant_id=tenant.id, user_id=user.id).one()
    assert order.status == "PENDING"
    assert order.points == 5000
    assert order.amount_cents == 4900


def test_recharge_order_rejects_unknown_package(session):
    tenant, user, _ = seed_account(session)
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/payments/recharge-orders",
        headers={"X-Tenant-ID": tenant.id},
        json={"user_id": user.id, "package_key": "unknown"},
    )

    assert response.status_code == 400
    assert "package" in response.json()["detail"]
    assert session.query(PaymentOrder).count() == 0
