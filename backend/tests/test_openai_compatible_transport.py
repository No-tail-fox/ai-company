import base64

import httpx

from app.models import ApiChannel, ChannelRoute, Tenant
from app.services.channel_router import HttpChannelTransport


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    calls = []
    responses = []

    def __init__(self, *, timeout):
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def post(self, url, json, headers):
        self.calls.append({"method": "post", "url": url, "json": json, "headers": headers, "timeout": self.timeout})
        return FakeResponse(self.responses.pop(0))

    def get(self, url, headers):
        self.calls.append({"method": "get", "url": url, "headers": headers, "timeout": self.timeout})
        return FakeResponse(self.responses.pop(0))


def route(channel_type: str, model: str = "provider-model") -> ChannelRoute:
    return ChannelRoute(
        tenant_id="tenant-a",
        route_key=f"{channel_type.lower()}_route",
        display_name=channel_type,
        backend_model=model,
        channel_type=channel_type,
        unit_cost=1,
        enabled=True,
    )


def channel(channel_type: str) -> ApiChannel:
    return ApiChannel(
        tenant_id="tenant-a",
        channel_key=f"{channel_type.lower()}-channel",
        display_name=channel_type,
        base_url="https://api.openai.com/v1/",
        api_key="secret",
        channel_type=channel_type,
        adapter_type="openai_compatible",
        timeout_seconds=33,
        enabled=True,
    )


def test_openai_compatible_text_uses_responses_api(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [{"id": "resp_1", "output_text": "hello"}]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    raw = HttpChannelTransport().send(
        channel("TEXT"),
        route("TEXT", "gpt-4.1-mini"),
        {"messages": [{"role": "user", "content": "Hi"}], "preset_role": "assistant"},
    )

    assert raw["content"] == "hello"
    call = FakeClient.calls[0]
    assert call["url"] == "https://api.openai.com/v1/responses"
    assert call["json"]["model"] == "gpt-4.1-mini"
    assert call["json"]["input"] == [{"role": "user", "content": "Hi"}]
    assert call["json"]["instructions"] == "assistant"
    assert call["headers"]["Authorization"] == "Bearer secret"


def test_openai_compatible_image_normalizes_url_result(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [{"data": [{"url": "https://cdn.example.com/image.png"}]}]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    raw = HttpChannelTransport().send(
        channel("IMAGE"),
        route("IMAGE", "gpt-image-1"),
        {"prompt": "product poster", "options": {"size": "1024x1024", "quality": "high", "n": 2}},
    )

    assert raw["result_url"] == "https://cdn.example.com/image.png"
    call = FakeClient.calls[0]
    assert call["url"] == "https://api.openai.com/v1/images/generations"
    assert call["json"] == {"model": "gpt-image-1", "prompt": "product poster", "size": "1024x1024", "quality": "high", "n": 2}


def test_openai_compatible_audio_speech_normalizes_result_url(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [{"url": "https://cdn.example.com/audio.mp3"}]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    raw = HttpChannelTransport().send(
        channel("AUDIO"),
        route("AUDIO", "gpt-4o-mini-tts"),
        {"task_type": "TTS", "prompt": "hello", "options": {"voice": "alloy", "speed": 1.1}},
    )

    assert raw["result_url"] == "https://cdn.example.com/audio.mp3"
    call = FakeClient.calls[0]
    assert call["url"] == "https://api.openai.com/v1/audio/speech"
    assert call["json"]["input"] == "hello"
    assert call["json"]["voice"] == "alloy"


def test_openai_compatible_video_create_and_poll(monkeypatch):
    FakeClient.calls = []
    FakeClient.responses = [
        {"id": "video_1", "status": "queued"},
        {"id": "video_1", "status": "completed", "url": "https://cdn.example.com/video.mp4"},
    ]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    created = HttpChannelTransport().send(
        channel("VIDEO"),
        route("VIDEO", "sora-2"),
        {"action": "create", "prompt": "launch video", "options": {"size": "1280x720", "seconds": 8}},
    )
    polled = HttpChannelTransport().send(
        channel("VIDEO"),
        route("VIDEO", "sora-2"),
        {"action": "status", "provider_task_id": "video_1"},
    )

    assert created["provider_task_id"] == "video_1"
    assert created["status"] == "QUEUED"
    assert polled["status"] == "COMPLETED"
    assert polled["result_url"] == "https://cdn.example.com/video.mp4"
    assert FakeClient.calls[0]["url"] == "https://api.openai.com/v1/videos"
    assert FakeClient.calls[1]["url"] == "https://api.openai.com/v1/videos/video_1"


def test_openai_compatible_image_saves_base64_result_to_storage(monkeypatch, tmp_path):
    FakeClient.calls = []
    FakeClient.responses = [{"data": [{"b64_json": base64.b64encode(b"png-bytes").decode("ascii")}]}]
    monkeypatch.setattr(httpx, "Client", FakeClient)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path))

    raw = HttpChannelTransport().send(channel("IMAGE"), route("IMAGE"), {"tenant_id": "tenant-a", "task_id": "task-a", "prompt": "poster"})

    assert raw["result_url"].startswith("/storage/generated/tenant-a/")
    assert (tmp_path / raw["storage_key"]).read_bytes() == b"png-bytes"

