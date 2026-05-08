from app.models import Asset, ChannelRoute, Tenant, User, Wallet
from app.services.generation import GenerationService
from app.services.payments import PaymentService


def test_payment_callback_is_idempotent(session):
    tenant = Tenant(id="tenant-acme", slug="acme", name="Acme")
    user = User(id="user-acme", tenant_id=tenant.id, phone="13800000000", role="USER")
    wallet = Wallet(id="wallet-acme", tenant_id=tenant.id, user_id=user.id, balance=0, frozen_balance=0)
    session.add_all([tenant, user, wallet])
    session.commit()

    service = PaymentService(session)

    first = service.handle_success_callback(
        tenant_id=tenant.id,
        user_id=user.id,
        provider="wechat",
        provider_order_no="WX-20260507-001",
        amount_cents=990,
        points=10000,
        request_key="pay-1",
        raw_payload={"status": "paid"},
    )
    second = service.handle_success_callback(
        tenant_id=tenant.id,
        user_id=user.id,
        provider="wechat",
        provider_order_no="WX-20260507-001",
        amount_cents=990,
        points=10000,
        request_key="pay-1",
        raw_payload={"status": "paid"},
    )

    assert first.id == second.id
    assert wallet.balance == 10000


def test_generation_completion_creates_asset_and_settles_wallet(session):
    tenant = Tenant(id="tenant-acme", slug="acme", name="Acme")
    user = User(id="user-acme", tenant_id=tenant.id, phone="13800000000", role="USER")
    wallet = Wallet(id="wallet-acme", tenant_id=tenant.id, user_id=user.id, balance=1000, frozen_balance=0)
    route = ChannelRoute(
        id="route-image",
        tenant_id=tenant.id,
        route_key="midjourney_image",
        display_name="Image",
        backend_model="midjourney-v6",
        channel_type="IMAGE",
        unit_cost=200,
        enabled=True,
    )
    session.add_all([tenant, user, wallet, route])
    session.commit()

    service = GenerationService(session)
    task = service.create_task(
        tenant_id=tenant.id,
        user_id=user.id,
        task_type="IMAGE",
        prompt="night city skyline",
        route_key="midjourney_image",
        estimated_cost=200,
        request_key="gen-1",
    )
    finished = service.complete_task(
        tenant_id=tenant.id,
        task_id=task.id,
        status="SUCCESS",
        actual_cost=50,
        result_url="https://cdn.example.com/art.png",
    )

    assert finished.status == "SUCCESS"
    assert wallet.balance == 950
    assert wallet.frozen_balance == 0
    assert session.query(Asset).count() == 1
