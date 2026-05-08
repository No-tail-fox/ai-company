from app.models import ApiChannel, ChannelRoute, Tenant
from app.services.channel_router import ChannelRouter


class FakeTransport:
    def __init__(self):
        self.calls = []

    def send(self, channel, route, payload):
        self.calls.append((channel.channel_key, route.route_key))
        if channel.channel_key == "primary":
            raise TimeoutError("primary failed")
        return {"provider_task_id": "abc-123", "result_url": "https://cdn.example.com/item.mp3"}


def test_router_falls_back_to_secondary_channel(session):
    tenant = Tenant(id="tenant-acme", slug="acme", name="Acme")
    route = ChannelRoute(
        id="route-1",
        tenant_id=tenant.id,
        route_key="suno_music",
        display_name="Music",
        backend_model="suno-v3",
        channel_type="AUDIO",
        unit_cost=200,
        enabled=True,
    )
    primary = ApiChannel(
        id="channel-primary",
        tenant_id=tenant.id,
        channel_key="primary",
        display_name="Primary",
        base_url="https://primary.example.com",
        api_key="secret-a",
        channel_type="AUDIO",
        priority=1,
        enabled=True,
    )
    secondary = ApiChannel(
        id="channel-secondary",
        tenant_id=tenant.id,
        channel_key="secondary",
        display_name="Secondary",
        base_url="https://secondary.example.com",
        api_key="secret-b",
        channel_type="AUDIO",
        priority=2,
        enabled=True,
    )
    session.add_all([tenant, route, primary, secondary])
    session.commit()

    router = ChannelRouter(session, FakeTransport())
    result = router.dispatch(
        tenant_id=tenant.id,
        route_key="suno_music",
        payload={"prompt": "cyberpunk anthem"},
    )

    assert result.channel_key == "secondary"
    assert result.provider_task_id == "abc-123"
    assert result.result_url == "https://cdn.example.com/item.mp3"
