from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import Tenant, User, Wallet
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def seed_tenant(session, tenant_id="tenant-auth"):
    tenant = Tenant(id=tenant_id, slug=tenant_id, name="Tenant Auth")
    session.add(tenant)
    session.commit()
    return tenant


def test_user_register_login_reset_and_change_password_flow(session):
    tenant = seed_tenant(session)
    client = make_client(session)

    verification = client.post(
        "/api/v1/auth/verification-codes",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "purpose": "REGISTER"},
    )
    assert verification.status_code == 200
    assert verification.json()["dev_code"] == "123456"

    registered = client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant.id},
        json={
            "phone": "13800000001",
            "password": "user123456",
            "display_name": "New User",
            "verification_code": "123456",
        },
    )
    assert registered.status_code == 201
    payload = registered.json()
    assert payload["access_token"]
    assert payload["user"]["role"] == "USER"
    assert payload["user"]["display_name"] == "New User"
    user = session.query(User).filter_by(tenant_id=tenant.id, phone="13800000001").one()
    assert session.query(Wallet).filter_by(tenant_id=tenant.id, user_id=user.id).one().balance == 0

    duplicate = client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant.id},
        json={
            "phone": "13800000001",
            "password": "user123456",
            "display_name": "Duplicate",
            "verification_code": "123456",
        },
    )
    assert duplicate.status_code == 400

    missing_code_login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "password": "user123456"},
    )
    assert missing_code_login.status_code == 400
    assert "verification" in missing_code_login.json()["detail"]

    login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "password": "user123456", "verification_code": "123456"},
    )
    assert login.status_code == 200
    user_token = login.json()["access_token"]

    reset = client.post(
        "/api/v1/auth/password/reset",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "verification_code": "123456", "new_password": "reset123456"},
    )
    assert reset.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "password": "user123456", "verification_code": "123456"},
    )
    assert old_login.status_code == 401

    change = client.post(
        "/api/v1/auth/password/change",
        headers={"X-Tenant-ID": tenant.id, "Authorization": f"Bearer {user_token}"},
        json={"current_password": "reset123456", "new_password": "changed123456"},
    )
    assert change.status_code == 200

    changed_login = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13800000001", "password": "changed123456", "verification_code": "123456"},
    )
    assert changed_login.status_code == 200


def test_admin_password_login_does_not_require_verification_code(session):
    tenant = seed_tenant(session)
    admin = User(
        id="admin-auth",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="Admin",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add(admin)
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant.id},
        json={"phone": "13900000000", "password": "admin123456"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "ADMIN"
