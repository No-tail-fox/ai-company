from __future__ import annotations

from typing import Any

from app.celery_app import celery_app
from app.db import SessionLocal
from app.services.feishu_import import FeishuImportService
from app.settings import get_settings


def enqueue_feishu_wiki_sync(
    *,
    tenant_id: str,
    actor_user_id: str,
    space_id: str,
    root_node_token: str,
    required_membership: bool,
) -> bool:
    if not get_settings().celery_enabled:
        return False
    try:
        process_feishu_wiki_sync.apply_async(
            kwargs={
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "space_id": space_id,
                "root_node_token": root_node_token,
                "required_membership": required_membership,
            },
            retry=False,
        )
    except Exception:
        return False
    return True


@celery_app.task(bind=True, name="feishu.wiki.sync")
def process_feishu_wiki_sync(
    self,
    *,
    tenant_id: str,
    actor_user_id: str,
    space_id: str,
    root_node_token: str,
    required_membership: bool,
) -> dict[str, Any]:
    del self
    with SessionLocal() as session:
        return FeishuImportService(session).sync_wiki(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            space_id=space_id,
            root_node_token=root_node_token,
            required_membership=required_membership,
        )


__all__ = ["enqueue_feishu_wiki_sync", "process_feishu_wiki_sync"]
