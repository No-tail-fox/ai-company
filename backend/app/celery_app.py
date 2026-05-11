from __future__ import annotations

from app.settings import get_settings

try:
    from celery import Celery
except ModuleNotFoundError:  # pragma: no cover - exercised only in lean local test envs.
    Celery = None  # type: ignore[assignment]


class _MissingCeleryTask:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def delay(self, *args, **kwargs):
        raise RuntimeError("celery is not installed")

    def apply_async(self, *args, **kwargs):
        raise RuntimeError("celery is not installed")


class _MissingCeleryApp:
    def task(self, *args, **kwargs):
        del args, kwargs

        def decorator(func):
            return _MissingCeleryTask(func)

        return decorator


settings = get_settings()

if Celery is None:
    celery_app = _MissingCeleryApp()
else:
    celery_app = Celery(
        "ai_company",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks.generation"],
    )

    celery_app.conf.update(
        accept_content=["json"],
        result_serializer="json",
        task_serializer="json",
        task_track_started=True,
        timezone="UTC",
    )


__all__ = ["celery_app"]
