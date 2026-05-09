from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.db import get_session, init_db
from app.models import User
from app.schemas import (
    AudioTaskCreate,
    AssistantCreate,
    ContentItemCreate,
    ContentItemUpdate,
    ContentPageCreate,
    ContentPageUpdate,
    ContentSectionCreate,
    ContentSectionUpdate,
    ImageGenerationCreate,
    ImageTaskPayload,
    ImageWorkbenchPayload,
    LoginRequest,
    ReorderRequest,
    VideoGenerationCreate,
    VideoTaskPayload,
    VideoWorkbenchPayload,
)
from app.seed import ensure_demo_data
from app.services.audio import AudioProviderError, AudioService
from app.services.admin_content import AdminContentService
from app.services.auth import AuthService
from app.services.channel_router import ChannelTransport, HttpChannelTransport, RouteNotFoundError
from app.services.image import DEMO_IMAGE_USER_ID, ImageService, ImageUserNotFoundError, ImageValidationError
from app.services.memberships import MembershipService
from app.services.portal import PortalService
from app.services.uploads import UploadService, UploadValidationError
from app.services.video import DEMO_VIDEO_USER_ID, VideoService, VideoUserNotFoundError, VideoValidationError
from app.services.wallet import InsufficientBalanceError, WalletNotFoundError
from app.settings import get_settings


TenantHeader = Annotated[str, Header(alias="X-Tenant-ID")]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


@contextmanager
def session_scope() -> Iterator[Session]:
    iterator = get_session()
    db = next(iterator)
    try:
        yield db
    finally:
        try:
            next(iterator)
        except StopIteration:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> Iterator[None]:
    init_db()
    with session_scope() as db:
        ensure_demo_data(db, tenant_id="demo")
    yield


def create_app(*, audio_transport: ChannelTransport | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.audio_transport = audio_transport or HttpChannelTransport()
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(f"{settings.api_prefix}/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(f"{settings.api_prefix}/portal/config")
    def portal_config(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        return PortalService(db).get_portal_config(tenant_id=tenant_id)

    @app.get(f"{settings.api_prefix}/portal/pages/{{page_key}}")
    def portal_page(
        page_key: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        payload = PortalService(db).get_page_config(tenant_id=tenant_id, page_key=page_key)
        if payload is None:
            raise HTTPException(status_code=404, detail="page not found")
        return payload

    @app.get(f"{settings.api_prefix}/assistants")
    def assistant_center(
        tenant_id: TenantHeader,
        category: str | None = None,
        db: Session = Depends(get_session),
    ) -> dict:
        return PortalService(db).get_assistant_center(tenant_id=tenant_id, category=category)

    @app.get(f"{settings.api_prefix}/video/workbench", response_model=VideoWorkbenchPayload)
    def video_workbench(
        tenant_id: TenantHeader,
        user_id: str = DEMO_VIDEO_USER_ID,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return VideoService(db).get_workbench(tenant_id=tenant_id, user_id=user_id)
        except (RouteNotFoundError, WalletNotFoundError, VideoUserNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/video/generations", status_code=status.HTTP_201_CREATED, response_model=VideoTaskPayload)
    def create_video_generation(
        payload: VideoGenerationCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return VideoService(db).create_generation(tenant_id=tenant_id, payload=payload)
        except (RouteNotFoundError, WalletNotFoundError, VideoUserNotFoundError, VideoValidationError, InsufficientBalanceError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/image/workbench", response_model=ImageWorkbenchPayload)
    def image_workbench(
        tenant_id: TenantHeader,
        user_id: str = DEMO_IMAGE_USER_ID,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ImageService(db).get_workbench(tenant_id=tenant_id, user_id=user_id)
        except (RouteNotFoundError, WalletNotFoundError, ImageUserNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/image/generations", status_code=status.HTTP_201_CREATED, response_model=ImageTaskPayload)
    def create_image_generation(
        payload: ImageGenerationCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ImageService(db).create_generation(tenant_id=tenant_id, payload=payload)
        except (RouteNotFoundError, WalletNotFoundError, ImageUserNotFoundError, ImageValidationError, InsufficientBalanceError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/memberships/status")
    def membership_status(
        tenant_id: TenantHeader,
        user_id: str,
        db: Session = Depends(get_session),
    ) -> dict:
        return MembershipService(db).get_status(tenant_id=tenant_id, user_id=user_id)

    @app.post(f"{settings.api_prefix}/auth/login")
    def login(
        payload: LoginRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        service = AuthService(db)
        user = service.authenticate(tenant_id=tenant_id, phone=payload.phone, password=payload.password)
        if user is None:
            raise HTTPException(status_code=401, detail="invalid phone or password")
        return {
            "access_token": service.create_access_token(user),
            "token_type": "bearer",
            "user": user_payload(user),
        }

    def require_admin(
        tenant_id: TenantHeader,
        authorization: AuthorizationHeader = None,
        db: Session = Depends(get_session),
    ) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="missing bearer token")
        token = authorization.removeprefix("Bearer ").strip()
        user = AuthService(db).user_from_token(tenant_id=tenant_id, token=token)
        if user is None:
            raise HTTPException(status_code=401, detail="invalid bearer token")
        if user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="admin role required")
        return user

    @app.get(f"{settings.api_prefix}/admin/pages")
    def list_pages(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        return [PortalService._page_payload(page) for page in AdminContentService(db).list_pages(tenant_id=tenant_id)]

    @app.post(f"{settings.api_prefix}/admin/pages", status_code=status.HTTP_201_CREATED)
    def create_page(
        payload: ContentPageCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        page = AdminContentService(db).create_page(tenant_id=tenant_id, payload=payload)
        return PortalService._page_payload(page)

    @app.post(f"{settings.api_prefix}/admin/pages/reorder")
    def reorder_pages(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        try:
            pages = AdminContentService(db).reorder_pages(tenant_id=tenant_id, ordered_ids=payload.ordered_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [PortalService._page_payload(page) for page in pages]

    @app.get(f"{settings.api_prefix}/admin/page-content/{{page_key}}")
    def admin_page_content(
        page_key: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            page, sections, items_by_section = AdminContentService(db).get_page_content(
                tenant_id=tenant_id,
                page_key=page_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        service = PortalService(db)
        return {
            "tenant_id": tenant_id,
            "page": PortalService._page_payload(page),
            "sections": [
                service._section_payload(section, items_by_section.get(section.id, []))
                for section in sections
            ],
        }

    @app.put(f"{settings.api_prefix}/admin/pages/{{page_id}}")
    def update_page(
        page_id: str,
        payload: ContentPageUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            page = AdminContentService(db).update_page(tenant_id=tenant_id, page_id=page_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._page_payload(page)

    @app.delete(f"{settings.api_prefix}/admin/pages/{{page_id}}")
    def delete_page(
        page_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            page = AdminContentService(db).disable_page(tenant_id=tenant_id, page_id=page_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._page_payload(page)

    @app.get(f"{settings.api_prefix}/admin/sections")
    def list_sections(
        tenant_id: TenantHeader,
        page_key: str | None = None,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        service = PortalService(db)
        return [service._section_payload(section, []) for section in AdminContentService(db).list_sections(tenant_id=tenant_id, page_key=page_key)]

    @app.post(f"{settings.api_prefix}/admin/sections", status_code=status.HTTP_201_CREATED)
    def create_section(
        payload: ContentSectionCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            section = AdminContentService(db).create_section(tenant_id=tenant_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._section_payload(section, [])

    @app.post(f"{settings.api_prefix}/admin/sections/reorder")
    def reorder_sections(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        try:
            sections = AdminContentService(db).reorder_sections(tenant_id=tenant_id, ordered_ids=payload.ordered_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        service = PortalService(db)
        return [service._section_payload(section, []) for section in sections]

    @app.put(f"{settings.api_prefix}/admin/sections/{{section_id}}")
    def update_section(
        section_id: str,
        payload: ContentSectionUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            section = AdminContentService(db).update_section(tenant_id=tenant_id, section_id=section_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._section_payload(section, [])

    @app.delete(f"{settings.api_prefix}/admin/sections/{{section_id}}")
    def delete_section(
        section_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            section = AdminContentService(db).disable_section(tenant_id=tenant_id, section_id=section_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._section_payload(section, [])

    @app.get(f"{settings.api_prefix}/admin/items")
    def list_items(
        tenant_id: TenantHeader,
        section_id: str | None = None,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        return [PortalService._item_payload(item) for item in AdminContentService(db).list_items(tenant_id=tenant_id, section_id=section_id)]

    @app.post(f"{settings.api_prefix}/admin/content/items", status_code=status.HTTP_201_CREATED)
    def create_content_item(
        payload: ContentItemCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            item = AdminContentService(db).create_content_item(tenant_id=tenant_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/items", status_code=status.HTTP_201_CREATED)
    def create_item(
        payload: ContentItemCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            item = AdminContentService(db).create_content_item(tenant_id=tenant_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/items/reorder")
    def reorder_items(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        if not payload.section_id:
            raise HTTPException(status_code=400, detail="section_id is required")
        try:
            items = AdminContentService(db).reorder_items(
                tenant_id=tenant_id,
                section_id=payload.section_id,
                ordered_ids=payload.ordered_ids,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [PortalService._item_payload(item) for item in items]

    @app.put(f"{settings.api_prefix}/admin/items/{{item_id}}")
    def update_item(
        item_id: str,
        payload: ContentItemUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            item = AdminContentService(db).update_content_item(tenant_id=tenant_id, item_id=item_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._item_payload(item)

    @app.delete(f"{settings.api_prefix}/admin/items/{{item_id}}")
    def delete_item(
        item_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            item = AdminContentService(db).disable_content_item(tenant_id=tenant_id, item_id=item_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/uploads", status_code=status.HTTP_201_CREATED)
    async def upload_image(
        tenant_id: TenantHeader,
        file: UploadFile = File(...),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        try:
            return await UploadService().save_image(tenant_id=tenant_id, upload=file)
        except UploadValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/audio/uploads", status_code=status.HTTP_201_CREATED)
    async def upload_audio(
        tenant_id: TenantHeader,
        file: UploadFile = File(...),
    ) -> dict:
        try:
            return await UploadService().save_audio(tenant_id=tenant_id, upload=file)
        except UploadValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/audio/tasks", status_code=status.HTTP_201_CREATED)
    def create_audio_task(
        payload: AudioTaskCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return AudioService(db, app.state.audio_transport).create_task(tenant_id=tenant_id, payload=payload)
        except RouteNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (InsufficientBalanceError, WalletNotFoundError) as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc
        except AudioProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/audio/tasks")
    def list_audio_tasks(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        return AudioService(db, app.state.audio_transport).list_tasks(tenant_id=tenant_id)

    @app.post(f"{settings.api_prefix}/admin/assistants", status_code=status.HTTP_201_CREATED)
    def create_assistant(
        payload: AssistantCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        assistant = AdminContentService(db).create_assistant(tenant_id=tenant_id, payload=payload)
        return PortalService(db)._assistant_payload(assistant)

    return app


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "phone": user.phone,
        "display_name": user.display_name,
        "role": user.role,
        "status": user.status,
    }


app = create_app()
