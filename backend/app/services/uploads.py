from __future__ import annotations

import os
from pathlib import Path
import re
import uuid

from fastapi import UploadFile

from app.settings import get_settings


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class UploadValidationError(ValueError):
    pass


class UploadService:
    def __init__(self, storage_dir: str | None = None):
        self.storage_dir = Path(storage_dir or os.environ.get("STORAGE_DIR") or get_settings().storage_dir)

    async def save_image(self, *, tenant_id: str, upload: UploadFile) -> dict:
        suffix = ALLOWED_IMAGE_TYPES.get(upload.content_type or "")
        if suffix is None:
            raise UploadValidationError("only jpeg, png, webp and gif uploads are allowed")

        content = await upload.read()
        if len(content) > MAX_UPLOAD_BYTES:
            raise UploadValidationError("image must be 5MB or smaller")

        safe_name = _safe_filename(upload.filename or "upload")
        if not safe_name.lower().endswith(suffix):
            safe_name = f"{Path(safe_name).stem}{suffix}"
        relative = Path("uploads") / tenant_id / f"{uuid.uuid4().hex}-{safe_name}"
        target = self.storage_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        storage_key = relative.as_posix()
        return {
            "filename": safe_name,
            "content_type": upload.content_type,
            "size": len(content),
            "storage_key": storage_key,
            "url": f"/storage/{storage_key}",
        }


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return cleaned or "upload"
