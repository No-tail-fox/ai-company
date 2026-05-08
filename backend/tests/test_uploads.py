from pathlib import Path

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import Tenant, User
from app.services.auth import hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def admin_headers(client: TestClient, tenant_id: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-ID": tenant_id},
        json={"phone": "13900000000", "password": "admin123456"},
    )
    assert response.status_code == 200
    return {"X-Tenant-ID": tenant_id, "Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_upload_saves_image_and_returns_public_url(session, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add_all([tenant, admin])
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/admin/uploads",
        headers=admin_headers(client, tenant.id),
        files={"file": ("banner.png", b"\x89PNG\r\n\x1a\nimage-content", "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["url"].startswith("/storage/uploads/tenant-a/")
    saved = tmp_path / payload["storage_key"]
    assert saved.exists()
    assert saved.read_bytes().startswith(b"\x89PNG")


def test_admin_upload_rejects_non_image_files(session, tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    admin = User(
        id="admin-a",
        tenant_id=tenant.id,
        phone="13900000000",
        display_name="管理员",
        role="ADMIN",
        password_hash=hash_password("admin123456"),
    )
    session.add_all([tenant, admin])
    session.commit()
    client = make_client(session)

    response = client.post(
        "/api/v1/admin/uploads",
        headers=admin_headers(client, tenant.id),
        files={"file": ("payload.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert not list(Path(tmp_path).rglob("payload.txt"))
