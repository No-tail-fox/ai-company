from fastapi.testclient import TestClient

from app.db import get_session
from app.main import create_app
from app.models import ContentItem, PortalDetailDocument, PortalDetailVersion, Tenant, User, UserPortalAction
from app.seed import ensure_demo_data
from app.services.auth import AuthService, hash_password


def override_session(session):
    def _override():
        yield session

    return _override


def make_client(session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_session] = override_session(session)
    return TestClient(app)


def bearer(session, tenant_id: str, user_id: str) -> dict[str, str]:
    user = session.get(User, user_id)
    assert user is not None
    return {"Authorization": f"Bearer {AuthService(session).create_access_token(user)}", "X-Tenant-ID": tenant_id}


def test_demo_seed_persists_communication_posts_and_details(session):
    ensure_demo_data(session, tenant_id="demo")
    client = make_client(session)

    hall = client.get("/api/v1/communication/posts?user_id=demo-user", headers={"X-Tenant-ID": "demo"})
    detail = client.get(
        "/api/v1/portal/details/communication/detail/tool-benefits-v14?user_id=demo-user",
        headers={"X-Tenant-ID": "demo"},
    )

    assert hall.status_code == 200
    posts = hall.json()["posts"]
    assert len(posts) >= 9
    assert posts[0]["detail_path"].startswith("/communication/detail/")
    assert any(post["id"] == "tool-benefits-v14" for post in posts)
    assert detail.status_code == 200
    assert detail.json()["detail"]["body_markdown"]
    assert session.query(ContentItem).filter_by(
        tenant_id="demo",
        item_type="communication_post",
        action_value="/communication/detail/tool-benefits-v14",
    ).count() == 1


def test_communication_post_requires_login_and_creates_detail_document(session):
    tenant = Tenant(id="tenant-a", slug="tenant-a", name="Tenant A")
    user = User(
        id="author-a",
        tenant_id=tenant.id,
        phone="13800000000",
        display_name="Author",
        role="USER",
        password_hash=hash_password("user123456"),
    )
    session.add_all([tenant, user])
    session.commit()
    client = make_client(session)

    anonymous = client.post(
        "/api/v1/communication/posts",
        headers={"X-Tenant-ID": tenant.id},
        json={"category_key": "talk", "title": "RAG project notes", "body_markdown": "First version"},
    )
    created = client.post(
        "/api/v1/communication/posts",
        headers=bearer(session, tenant.id, user.id),
        json={"category_key": "talk", "title": "RAG project notes", "body_markdown": "First version"},
    )

    assert anonymous.status_code == 401
    assert created.status_code == 201
    post = created.json()["post"]
    assert post["detail_path"].startswith("/communication/detail/rag-project-notes")
    assert post["is_favorite"] is False
    assert session.query(ContentItem).filter_by(tenant_id=tenant.id, item_type="communication_post").count() == 1
    assert session.query(PortalDetailDocument).filter_by(tenant_id=tenant.id, detail_path=post["detail_path"]).count() == 1
    assert session.query(PortalDetailVersion).count() == 1

    detail = client.get(
        f"/api/v1/portal/details/{post['detail_path'].lstrip('/')}?user_id={user.id}",
        headers={"X-Tenant-ID": tenant.id},
    )
    assert detail.status_code == 200
    assert detail.json()["detail"]["body_markdown"] == "First version"


def test_communication_hall_reflects_favorite_actions(session):
    ensure_demo_data(session, tenant_id="demo")
    client = make_client(session)
    path = "/communication/detail/tool-benefits-v14"
    item = session.query(ContentItem).filter_by(tenant_id="demo", action_value=path).one()
    session.add(
        UserPortalAction(
            tenant_id="demo",
            user_id="demo-user",
            detail_path=path,
            item_id=item.id,
            action_key="favorite",
            status="COMPLETED",
        )
    )
    session.commit()

    response = client.get("/api/v1/communication/posts?user_id=demo-user", headers={"X-Tenant-ID": "demo"})

    assert response.status_code == 200
    post = next(post for post in response.json()["posts"] if post["id"] == "tool-benefits-v14")
    assert post["is_favorite"] is True
