from types import SimpleNamespace

from app.models import ApiChannel, Asset, ChannelRoute, GenerationTask, Tenant, User, Wallet
from app.services.generation import GenerationService
from app.tasks import generation as generation_task_module
from app.tasks.generation import enqueue_generation_task, process_generation_task_once


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def send(self, channel, route, payload):
        self.calls.append({"channel": channel.channel_key, "route": route.route_key, "payload": payload})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_enqueue_generation_task_returns_false_when_queue_is_disabled(monkeypatch):
    monkeypatch.setattr(generation_task_module, "get_settings", lambda: SimpleNamespace(celery_enabled=False))

    assert enqueue_generation_task(tenant_id="tenant-a", task_id="task-a") is False


def test_enqueue_generation_task_returns_false_without_blocking_when_publish_fails(monkeypatch):
    calls = []

    def fail_publish(*, kwargs, retry):
        calls.append({"kwargs": kwargs, "retry": retry})
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(generation_task_module, "get_settings", lambda: SimpleNamespace(celery_enabled=True))
    monkeypatch.setattr(generation_task_module.process_generation_task, "apply_async", fail_publish)

    assert enqueue_generation_task(tenant_id="tenant-a", task_id="task-a") is False
    assert calls == [{"kwargs": {"tenant_id": "tenant-a", "task_id": "task-a"}, "retry": False}]


def seed_runtime(
    session,
    *,
    tenant_id="tenant-a",
    user_id="demo-user",
    task_type="IMAGE",
    route_key="image_text_to_image",
    channel_type="IMAGE",
    unit_cost=80,
):
    session.add(Tenant(id=tenant_id, slug=tenant_id, name="Tenant A"))
    session.add(User(id=user_id, tenant_id=tenant_id, phone="13800000000", role="USER"))
    wallet = Wallet(id=f"wallet-{tenant_id}", tenant_id=tenant_id, user_id=user_id, balance=1000, frozen_balance=0)
    route = ChannelRoute(
        id=f"route-{route_key}",
        tenant_id=tenant_id,
        route_key=route_key,
        display_name=route_key,
        backend_model=f"provider-{route_key}",
        channel_type=channel_type,
        unit_cost=unit_cost,
        enabled=True,
    )
    channel = ApiChannel(
        id=f"channel-{channel_type.lower()}",
        tenant_id=tenant_id,
        channel_key=f"{channel_type.lower()}-provider",
        display_name=f"{channel_type} Provider",
        base_url=f"https://{channel_type.lower()}.example.com/generate",
        api_key="secret",
        channel_type=channel_type,
        priority=1,
        enabled=True,
    )
    session.add_all([wallet, route, channel])
    session.commit()
    task = GenerationService(session).create_task(
        tenant_id=tenant_id,
        user_id=user_id,
        task_type=task_type,
        prompt="生成一张产品海报",
        route_key=route_key,
        estimated_cost=unit_cost,
        request_key=f"workbench:{task_type.lower()}-1",
    )
    return wallet, task


def test_generation_worker_completes_synchronous_provider_result_and_creates_asset(session):
    wallet, task = seed_runtime(session)
    transport = ScriptedTransport([{"provider_task_id": "provider-image-1", "result_url": "https://cdn.example.com/image.png"}])

    result = process_generation_task_once(session=session, tenant_id="tenant-a", task_id=task.id, transport=transport)

    saved_task = session.get(GenerationTask, task.id)
    assert result["status"] == "SUCCESS"
    assert saved_task.status == "SUCCESS"
    assert saved_task.result_url == "https://cdn.example.com/image.png"
    assert saved_task.actual_cost == 80
    assert wallet.balance == 920
    assert wallet.frozen_balance == 0
    assert session.query(Asset).filter_by(generation_task_id=task.id, asset_type="IMAGE").count() == 1
    assert transport.calls[0]["payload"]["action"] == "create"
    assert transport.calls[0]["payload"]["task_id"] == task.id
    assert transport.calls[0]["payload"]["model"] == "provider-image_text_to_image"


def test_generation_worker_polls_async_provider_task_until_success(session):
    wallet, task = seed_runtime(session)
    transport = ScriptedTransport(
        [
            {"provider_task_id": "provider-image-async", "status": "PROCESSING"},
            {"provider_task_id": "provider-image-async", "status": "SUCCESS", "result_url": "https://cdn.example.com/async.png"},
        ]
    )

    first = process_generation_task_once(session=session, tenant_id="tenant-a", task_id=task.id, transport=transport)
    second = process_generation_task_once(session=session, tenant_id="tenant-a", task_id=task.id, transport=transport)

    saved_task = session.get(GenerationTask, task.id)
    assert first["status"] == "PROCESSING"
    assert second["status"] == "SUCCESS"
    assert saved_task.provider_task_id == "provider-image-async"
    assert saved_task.result_url == "https://cdn.example.com/async.png"
    assert wallet.balance == 920
    assert wallet.frozen_balance == 0
    assert transport.calls[0]["payload"]["action"] == "create"
    assert transport.calls[1]["payload"]["action"] == "status"
    assert transport.calls[1]["payload"]["provider_task_id"] == "provider-image-async"


def test_generation_worker_marks_failure_and_releases_reserved_wallet_funds(session):
    wallet, task = seed_runtime(session)
    transport = ScriptedTransport([{"provider_task_id": "provider-image-failed", "status": "FAILED", "error_message": "bad prompt"}])

    result = process_generation_task_once(session=session, tenant_id="tenant-a", task_id=task.id, transport=transport)

    saved_task = session.get(GenerationTask, task.id)
    assert result["status"] == "FAILED"
    assert saved_task.status == "FAILED"
    assert saved_task.error_message == "bad prompt"
    assert saved_task.actual_cost == 0
    assert wallet.balance == 1000
    assert wallet.frozen_balance == 0
