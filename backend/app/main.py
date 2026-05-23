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
    AdminUserCreate,
    AdminUserUpdate,
    AccountProfileUpdate,
    AudioTaskCreate,
    AssistantCreate,
    ChatModelProfileUpdate,
    ChatExportCreate,
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
    CommunicationPostCreate,
    ContentItemCreate,
    ContentItemUpdate,
    ContentPageCreate,
    ContentPageUpdate,
    ContentSectionCreate,
    ContentSectionUpdate,
    FeishuBrowserSnapshotImport,
    FeishuWikiSyncCreate,
    GenerationSurface,
    ImageGenerationCreate,
    ImageTaskPayload,
    ImageWorkbenchPayload,
    HomeHeroSlideCreate,
    HomeHeroSlideUpdate,
    LoginRequest,
    MembershipPlanCreate,
    MembershipPlanUpdate,
    ModelConfigCreate,
    ModelConfigUpdate,
    PasswordChangeRequest,
    PasswordResetRequest,
    PortalActionCreate,
    PortalDetailCommentCreate,
    PortalDetailPublishCreate,
    PortalDetailUpdate,
    ProviderChannelCreate,
    ProviderChannelUpdate,
    RechargeOrderCreate,
    RedeemCodeRequest,
    RedemptionBatchCreate,
    RegisterRequest,
    UserMembershipCreate,
    UserMembershipUpdate,
    VerificationCodeCreate,
    WalletAdjustmentCreate,
    ReorderRequest,
    ToolModelBindingCreate,
    ToolModelBindingUpdate,
    VideoGenerationCreate,
    VideoTaskPayload,
    VideoWorkbenchPayload,
    WorkbenchCapabilityUpdate,
)
from app.seed import ensure_demo_data
from app.services.account import AccountNotFoundError, AccountService
from app.services.admin_management import AdminManagementService
from app.services.audio import AudioProviderError, AudioService
from app.services.chat import ChatNotFoundError, ChatProviderError, ChatService, ChatValidationError
from app.services.admin_content import AdminContentService
from app.services.auth import AuthService
from app.services.channel_router import ChannelTransport, HttpChannelTransport, RouteNotFoundError
from app.services.communication import CommunicationService
from app.services.feishu_import import CourseAdminService, CourseCatalogService, FeishuImportService
from app.services.image import DEMO_IMAGE_USER_ID, ImageService, ImageUserNotFoundError, ImageValidationError
from app.services.home_dashboard import HomeDashboardService
from app.services.memberships import MembershipService
from app.services.model_configs import ModelConfigError, ModelConfigService
from app.services.payments import PaymentPackageError, PaymentService, PaymentUserNotFoundError
from app.services.portal import PortalService
from app.services.rbac import has_min_role
from app.services.redemptions import RedemptionNotFoundError, RedemptionService, RedemptionValidationError
from app.services.uploads import UploadService, UploadValidationError
from app.services.video import DEMO_VIDEO_USER_ID, VideoService, VideoUserNotFoundError, VideoValidationError
from app.services.wallet import InsufficientBalanceError, WalletNotFoundError
from app.services.workbench_capabilities import WorkbenchCapabilityService
from app.settings import get_settings
from app.tasks.feishu_import import enqueue_feishu_wiki_sync


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


def create_app(*, audio_transport: ChannelTransport | None = None, chat_transport: ChannelTransport | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.audio_transport = audio_transport or HttpChannelTransport()
    app.state.chat_transport = chat_transport or HttpChannelTransport()
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
        if not has_min_role(user.role, "READ_ONLY"):
            raise HTTPException(status_code=403, detail="admin role required")
        return user

    def require_admin_role(admin: User, minimum_role: str) -> None:
        if not has_min_role(admin.role, minimum_role):
            raise HTTPException(status_code=403, detail=f"{minimum_role} role required")

    def require_user(
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
        return user

    def optional_user(
        tenant_id: TenantHeader,
        authorization: AuthorizationHeader = None,
        db: Session = Depends(get_session),
    ) -> User | None:
        if not authorization or not authorization.startswith("Bearer "):
            return None
        token = authorization.removeprefix("Bearer ").strip()
        return AuthService(db).user_from_token(tenant_id=tenant_id, token=token)

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

    @app.get(f"{settings.api_prefix}/portal/details/{{detail_path:path}}")
    def portal_detail(
        detail_path: str,
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        db: Session = Depends(get_session),
        actor: User | None = Depends(optional_user),
    ) -> dict:
        payload = PortalService(db).get_detail(tenant_id=tenant_id, detail_path=detail_path, user_id=user_id, actor=actor)
        if payload is None:
            raise HTTPException(status_code=404, detail="detail not found")
        return payload

    @app.patch(f"{settings.api_prefix}/portal/details/{{detail_path:path}}")
    def update_portal_detail(
        detail_path: str,
        payload: PortalDetailUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        actor: User = Depends(require_user),
    ) -> dict:
        try:
            return PortalService(db).update_detail(tenant_id=tenant_id, detail_path=detail_path, payload=payload, actor=actor)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/portal/details/{{detail_path:path}}/versions")
    def publish_portal_detail_version(
        detail_path: str,
        payload: PortalDetailPublishCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        actor: User = Depends(require_user),
    ) -> dict:
        try:
            return PortalService(db).publish_detail_version(tenant_id=tenant_id, detail_path=detail_path, payload=payload, actor=actor)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/portal/details/{{detail_path:path}}/versions/{{version_id}}/rollback")
    def rollback_portal_detail_version(
        detail_path: str,
        version_id: str,
        payload: PortalDetailPublishCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        actor: User = Depends(require_user),
    ) -> dict:
        try:
            return PortalService(db).rollback_detail_version(
                tenant_id=tenant_id,
                detail_path=detail_path,
                version_id=version_id,
                payload=payload,
                actor=actor,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/portal/details/{{detail_path:path}}/comments", status_code=status.HTTP_201_CREATED)
    def create_portal_detail_comment(
        detail_path: str,
        payload: PortalDetailCommentCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        actor: User = Depends(require_user),
    ) -> dict:
        try:
            return PortalService(db).create_detail_comment(tenant_id=tenant_id, detail_path=detail_path, payload=payload, actor=actor)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/portal/search")
    def portal_search(
        tenant_id: TenantHeader,
        q: str = "",
        page_key: str | None = None,
        limit: int = 8,
        db: Session = Depends(get_session),
    ) -> dict:
        return PortalService(db).search(tenant_id=tenant_id, query=q, page_key=page_key, limit=limit)

    @app.get(f"{settings.api_prefix}/home/dashboard")
    def home_dashboard(
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        db: Session = Depends(get_session),
    ) -> dict:
        return HomeDashboardService(db).dashboard(tenant_id=tenant_id, user_id=user_id)

    @app.post(f"{settings.api_prefix}/portal/actions")
    def portal_action(
        payload: PortalActionCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        return PortalService(db).perform_action(tenant_id=tenant_id, payload=payload)

    @app.get(f"{settings.api_prefix}/portal/user-actions")
    def portal_user_actions(
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        kind: str = "all",
        limit: int = 20,
        db: Session = Depends(get_session),
    ) -> dict:
        return PortalService(db).user_actions(tenant_id=tenant_id, user_id=user_id, kind=kind, limit=limit)

    @app.get(f"{settings.api_prefix}/courses")
    def course_catalog(
        tenant_id: TenantHeader,
        q: str = "",
        category: str = "",
        page: int = 1,
        page_size: int = 20,
        db: Session = Depends(get_session),
    ) -> dict:
        return CourseCatalogService(db).list_courses(
            tenant_id=tenant_id,
            query=q,
            category=category,
            page=page,
            page_size=page_size,
        )

    @app.get(f"{settings.api_prefix}/admin/courses")
    def admin_course_catalog(
        tenant_id: TenantHeader,
        q: str = "",
        category: str = "",
        page: int = 1,
        page_size: int = 50,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        return CourseAdminService(db).list_courses(
            tenant_id=tenant_id,
            query=q,
            category=category,
            page=page,
            page_size=page_size,
        )

    @app.post(f"{settings.api_prefix}/admin/courses/cleanup")
    def admin_cleanup_courses(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        return CourseAdminService(db).cleanup_courses(tenant_id=tenant_id)

    @app.get(f"{settings.api_prefix}/communication/posts")
    def communication_posts(
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        db: Session = Depends(get_session),
    ) -> dict:
        return CommunicationService(db).hall_payload(tenant_id=tenant_id, user_id=user_id)

    @app.post(f"{settings.api_prefix}/communication/posts", status_code=status.HTTP_201_CREATED)
    def create_communication_post(
        payload: CommunicationPostCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        actor: User = Depends(require_user),
    ) -> dict:
        try:
            return CommunicationService(db).create_post(tenant_id=tenant_id, payload=payload, actor=actor)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/overview")
    def admin_overview(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        return AdminManagementService(db).overview(tenant_id=tenant_id)

    @app.post(f"{settings.api_prefix}/admin/imports/feishu/wiki/sync")
    def start_feishu_wiki_sync(
        payload: FeishuWikiSyncCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        space_id = (payload.space_id or settings.feishu_wiki_space_id).strip()
        root_node_token = (payload.root_node_token or settings.feishu_wiki_root_node_token).strip()
        required_membership = settings.feishu_sync_required_membership if payload.required_membership is None else payload.required_membership
        if not space_id or not root_node_token:
            raise HTTPException(status_code=400, detail="space_id and root_node_token are required")
        if enqueue_feishu_wiki_sync(
            tenant_id=tenant_id,
            actor_user_id=admin.id,
            space_id=space_id,
            root_node_token=root_node_token,
            required_membership=required_membership,
        ):
            return {
                "queued": True,
                "run": {
                    "status": "QUEUED",
                    "space_id": space_id,
                    "root_node_token": root_node_token,
                    "stats": {"total": 0, "created": 0, "updated": 0, "skipped": 0, "unsupported": 0, "failed": 0},
                },
            }
        try:
            return {
                "queued": False,
                **FeishuImportService(db).sync_wiki(
                    tenant_id=tenant_id,
                    actor_user_id=admin.id,
                    space_id=space_id,
                    root_node_token=root_node_token,
                    required_membership=required_membership,
                ),
            }
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/imports/feishu/wiki/runs/{{run_id}}")
    def get_feishu_wiki_sync_run(
        run_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        payload = FeishuImportService(db).get_run(tenant_id=tenant_id, run_id=run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="sync run not found")
        return payload

    @app.post(f"{settings.api_prefix}/admin/imports/feishu/browser/snapshot")
    def import_feishu_browser_snapshot(
        payload: FeishuBrowserSnapshotImport,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        required_membership = settings.feishu_sync_required_membership if payload.required_membership is None else payload.required_membership
        try:
            return FeishuImportService(db).import_browser_snapshot(
                tenant_id=tenant_id,
                actor_user_id=admin.id,
                title=payload.title,
                source_url=payload.source_url,
                node_token=payload.node_token,
                source_path=payload.source_path,
                body_markdown=payload.body_markdown,
                asset_url_map=payload.asset_url_map,
                required_membership=required_membership,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/users")
    def list_admin_users(
        tenant_id: TenantHeader,
        query: str = "",
        role: str | None = None,
        status: str | None = None,
        limit: int = 100,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        users = AdminManagementService(db).list_users(tenant_id=tenant_id, query=query, role=role, status=status, limit=limit)
        return {"tenant_id": tenant_id, "users": users}

    @app.post(f"{settings.api_prefix}/admin/users", status_code=status.HTTP_201_CREATED)
    def create_admin_user(
        payload: AdminUserCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        return AdminManagementService(db).create_user(tenant_id=tenant_id, payload=payload, actor=admin)

    @app.put(f"{settings.api_prefix}/admin/users/{{user_id}}")
    def update_admin_user(
        user_id: str,
        payload: AdminUserUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).update_user(tenant_id=tenant_id, user_id=user_id, payload=payload, actor=admin)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(f"{settings.api_prefix}/admin/users/{{user_id}}")
    def delete_admin_user(
        user_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).disable_user(tenant_id=tenant_id, user_id=user_id, actor=admin)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/wallet-transactions")
    def list_wallet_transactions(
        tenant_id: TenantHeader,
        user_id: str | None = None,
        limit: int = 100,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        transactions = AdminManagementService(db).list_wallet_transactions(tenant_id=tenant_id, user_id=user_id, limit=limit)
        return {"tenant_id": tenant_id, "transactions": transactions}

    @app.post(f"{settings.api_prefix}/admin/wallets/{{user_id}}/adjust")
    def adjust_admin_wallet(
        user_id: str,
        payload: WalletAdjustmentCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).adjust_wallet(tenant_id=tenant_id, user_id=user_id, payload=payload, actor=admin)
        except WalletNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, InsufficientBalanceError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/membership-plans")
    def list_membership_plans(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        plans = AdminManagementService(db).list_membership_plans(tenant_id=tenant_id)
        return {"tenant_id": tenant_id, "plans": plans}

    @app.post(f"{settings.api_prefix}/admin/membership-plans", status_code=status.HTTP_201_CREATED)
    def create_membership_plan(
        payload: MembershipPlanCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).create_membership_plan(tenant_id=tenant_id, payload=payload, actor=admin)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put(f"{settings.api_prefix}/admin/membership-plans/{{plan_id}}")
    def update_membership_plan(
        plan_id: str,
        payload: MembershipPlanUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).update_membership_plan(
                tenant_id=tenant_id,
                plan_id=plan_id,
                payload=payload,
                actor=admin,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(f"{settings.api_prefix}/admin/membership-plans/{{plan_id}}")
    def delete_membership_plan(
        plan_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).disable_membership_plan(tenant_id=tenant_id, plan_id=plan_id, actor=admin)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/user-memberships")
    def list_user_memberships(
        tenant_id: TenantHeader,
        user_id: str | None = None,
        limit: int = 100,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        memberships = AdminManagementService(db).list_user_memberships(tenant_id=tenant_id, user_id=user_id, limit=limit)
        return {"tenant_id": tenant_id, "memberships": memberships}

    @app.post(f"{settings.api_prefix}/admin/user-memberships", status_code=status.HTTP_201_CREATED)
    def create_user_membership(
        payload: UserMembershipCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).grant_membership(tenant_id=tenant_id, payload=payload, actor=admin)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.put(f"{settings.api_prefix}/admin/user-memberships/{{membership_id}}")
    def update_user_membership(
        membership_id: str,
        payload: UserMembershipUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).update_user_membership(
                tenant_id=tenant_id,
                membership_id=membership_id,
                payload=payload,
                actor=admin,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(f"{settings.api_prefix}/admin/user-memberships/{{membership_id}}")
    def delete_user_membership(
        membership_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return AdminManagementService(db).disable_user_membership(
                tenant_id=tenant_id,
                membership_id=membership_id,
                actor=admin,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/audit-logs")
    def list_audit_logs(
        tenant_id: TenantHeader,
        limit: int = 50,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        logs = AdminManagementService(db).list_audit_logs(tenant_id=tenant_id, limit=limit)
        service = AdminManagementService(db)
        return {"tenant_id": tenant_id, "logs": [service.audit_log_payload(log) for log in logs]}

    @app.get(f"{settings.api_prefix}/admin/redemption-batches")
    def list_redemption_batches(
        tenant_id: TenantHeader,
        limit: int = 100,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        batches = RedemptionService(db).list_batches(tenant_id=tenant_id, limit=limit)
        return {"tenant_id": tenant_id, "batches": batches}

    @app.post(f"{settings.api_prefix}/admin/redemption-batches", status_code=status.HTTP_201_CREATED)
    def create_redemption_batch(
        payload: RedemptionBatchCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return RedemptionService(db).create_batch(tenant_id=tenant_id, payload=payload, actor=admin)
        except RedemptionValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/redemption-codes")
    def list_redemption_codes(
        tenant_id: TenantHeader,
        batch_id: str | None = None,
        limit: int = 200,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        codes = RedemptionService(db).list_codes(tenant_id=tenant_id, batch_id=batch_id, limit=limit)
        return {"tenant_id": tenant_id, "codes": codes}

    @app.delete(f"{settings.api_prefix}/admin/redemption-codes/{{code_id}}")
    def disable_redemption_code(
        code_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return RedemptionService(db).disable_code(tenant_id=tenant_id, code_id=code_id)
        except RedemptionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/account/summary")
    def account_summary(
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return AccountService(db).summary(tenant_id=tenant_id, user_id=user_id)
        except AccountNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.patch(f"{settings.api_prefix}/account/profile")
    def account_profile(
        payload: AccountProfileUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return AccountService(db).update_profile(
                tenant_id=tenant_id,
                user_id=payload.user_id,
                display_name=payload.display_name,
            )
        except AccountNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/redemptions/redeem")
    def redeem_code(
        payload: RedeemCodeRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        user: User = Depends(require_user),
    ) -> dict:
        try:
            return RedemptionService(db).redeem(tenant_id=tenant_id, user=user, code=payload.code)
        except RedemptionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RedemptionValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/payments/recharge-orders", status_code=status.HTTP_201_CREATED)
    def create_recharge_order(
        payload: RechargeOrderCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return PaymentService(db).create_recharge_order(
                tenant_id=tenant_id,
                user_id=payload.user_id,
                package_key=payload.package_key,
            )
        except PaymentPackageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PaymentUserNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/video/workbench", response_model=VideoWorkbenchPayload)
    def video_workbench(
        tenant_id: TenantHeader,
        user_id: str = DEMO_VIDEO_USER_ID,
        surface: GenerationSurface = "portal",
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return VideoService(db).get_workbench(tenant_id=tenant_id, user_id=user_id, surface=surface)
        except (RouteNotFoundError, WalletNotFoundError, VideoUserNotFoundError, ModelConfigError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/chat/workbench")
    def chat_workbench(
        tenant_id: TenantHeader,
        user_id: str = "demo-user",
        session_id: str | None = None,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).get_workbench(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ChatValidationError, ChatProviderError) as exc:
            raise HTTPException(status_code=400 if isinstance(exc, ChatValidationError) else 502, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/chat/sessions", status_code=status.HTTP_201_CREATED)
    def create_chat_session(
        payload: ChatSessionCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).create_session(tenant_id=tenant_id, payload=payload)
        except ChatValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/chat/sessions/{{session_id}}")
    def get_chat_session(
        session_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).get_session(tenant_id=tenant_id, session_id=session_id)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.patch(f"{settings.api_prefix}/chat/sessions/{{session_id}}")
    def update_chat_session(
        session_id: str,
        payload: ChatSessionUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).update_session(tenant_id=tenant_id, session_id=session_id, payload=payload)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ChatValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/chat/sessions/{{session_id}}/messages", status_code=status.HTTP_201_CREATED)
    def create_chat_message(
        session_id: str,
        payload: ChatMessageCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).send_message(tenant_id=tenant_id, session_id=session_id, payload=payload)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ChatValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ChatProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/chat/sessions/{{session_id}}/export", status_code=status.HTTP_201_CREATED)
    def export_chat_session(
        session_id: str,
        payload: ChatExportCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ChatService(db, app.state.chat_transport).export_session(tenant_id=tenant_id, session_id=session_id, payload=payload)
        except ChatNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ChatValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/video/generations", status_code=status.HTTP_201_CREATED, response_model=VideoTaskPayload)
    def create_video_generation(
        payload: VideoGenerationCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return VideoService(db).create_generation(tenant_id=tenant_id, payload=payload)
        except (RouteNotFoundError, WalletNotFoundError, VideoUserNotFoundError, VideoValidationError, InsufficientBalanceError, ModelConfigError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/image/workbench", response_model=ImageWorkbenchPayload)
    def image_workbench(
        tenant_id: TenantHeader,
        user_id: str = DEMO_IMAGE_USER_ID,
        surface: GenerationSurface = "portal",
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ImageService(db).get_workbench(tenant_id=tenant_id, user_id=user_id, surface=surface)
        except (RouteNotFoundError, WalletNotFoundError, ImageUserNotFoundError, ModelConfigError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/image/generations", status_code=status.HTTP_201_CREATED, response_model=ImageTaskPayload)
    def create_image_generation(
        payload: ImageGenerationCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return ImageService(db).create_generation(tenant_id=tenant_id, payload=payload)
        except (RouteNotFoundError, WalletNotFoundError, ImageUserNotFoundError, ImageValidationError, InsufficientBalanceError, ModelConfigError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/workbench/capabilities")
    def workbench_capabilities(
        tenant_id: TenantHeader,
        surface: GenerationSurface = "workbench",
        db: Session = Depends(get_session),
    ) -> dict:
        return WorkbenchCapabilityService(db).list_capabilities(tenant_id=tenant_id, surface=surface)

    @app.get(f"{settings.api_prefix}/memberships/status")
    def membership_status(
        tenant_id: TenantHeader,
        user_id: str,
        db: Session = Depends(get_session),
    ) -> dict:
        return MembershipService(db).get_status(tenant_id=tenant_id, user_id=user_id)

    @app.post(f"{settings.api_prefix}/auth/verification-codes")
    def create_verification_code(
        payload: VerificationCodeCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            return AuthService(db).create_verification_code(
                tenant_id=tenant_id,
                phone=payload.phone,
                purpose=payload.purpose,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(f"{settings.api_prefix}/auth/register", status_code=status.HTTP_201_CREATED)
    def register(
        payload: RegisterRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        service = AuthService(db)
        try:
            user = service.register_user(
                tenant_id=tenant_id,
                phone=payload.phone,
                password=payload.password,
                display_name=payload.display_name,
                verification_code=payload.verification_code,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "access_token": service.create_access_token(user),
            "token_type": "bearer",
            "user": user_payload(user),
        }

    @app.post(f"{settings.api_prefix}/auth/login")
    def login(
        payload: LoginRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        service = AuthService(db)
        login_method = payload.login_method.strip().upper()
        if login_method == "CODE":
            user = service.active_user_by_phone(tenant_id=tenant_id, phone=payload.phone)
            if user is None:
                raise HTTPException(status_code=401, detail="invalid phone or verification code")
            if has_min_role(user.role, "READ_ONLY"):
                raise HTTPException(status_code=400, detail="admin login requires password")
            if not service.verify_code(phone=payload.phone, purpose="LOGIN", verification_code=payload.verification_code):
                raise HTTPException(status_code=400, detail="verification code is invalid")
        elif login_method == "PASSWORD":
            if not payload.password:
                raise HTTPException(status_code=400, detail="password is required")
            user = service.authenticate(tenant_id=tenant_id, phone=payload.phone, password=payload.password)
            if user is None:
                raise HTTPException(status_code=401, detail="invalid phone or password")
        else:
            raise HTTPException(status_code=400, detail="unsupported login method")
        return {
            "access_token": service.create_access_token(user),
            "token_type": "bearer",
            "user": user_payload(user),
        }

    @app.post(f"{settings.api_prefix}/auth/password/reset")
    def reset_password(
        payload: PasswordResetRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
    ) -> dict:
        try:
            user = AuthService(db).reset_password(
                tenant_id=tenant_id,
                phone=payload.phone,
                verification_code=payload.verification_code,
                new_password=payload.new_password,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "UPDATED", "user": user_payload(user)}

    @app.post(f"{settings.api_prefix}/auth/password/change")
    def change_password(
        payload: PasswordChangeRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        user: User = Depends(require_user),
    ) -> dict:
        del tenant_id
        try:
            updated = AuthService(db).change_password(
                user=user,
                current_password=payload.current_password,
                new_password=payload.new_password,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "UPDATED", "user": user_payload(updated)}

    @app.get(f"{settings.api_prefix}/admin/chat-model-profile")
    def get_chat_model_profile(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        return ModelConfigService(db).get_chat_model_profile(tenant_id=tenant_id)

    @app.put(f"{settings.api_prefix}/admin/chat-model-profile")
    def update_chat_model_profile(
        payload: ChatModelProfileUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).upsert_chat_model_profile(tenant_id=tenant_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/provider-channels")
    def list_provider_channels(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        return ModelConfigService(db).list_provider_channels(tenant_id=tenant_id)

    @app.post(f"{settings.api_prefix}/admin/provider-channels", status_code=status.HTTP_201_CREATED)
    def create_provider_channel(
        payload: ProviderChannelCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).create_provider_channel(tenant_id=tenant_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put(f"{settings.api_prefix}/admin/provider-channels/{{channel_id}}")
    def update_provider_channel(
        channel_id: str,
        payload: ProviderChannelUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).update_provider_channel(tenant_id=tenant_id, channel_id=channel_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/model-configs")
    def list_model_configs(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        return ModelConfigService(db).list_model_configs(tenant_id=tenant_id)

    @app.post(f"{settings.api_prefix}/admin/model-configs", status_code=status.HTTP_201_CREATED)
    def create_model_config(
        payload: ModelConfigCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).create_model_config(tenant_id=tenant_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put(f"{settings.api_prefix}/admin/model-configs/{{model_config_id}}")
    def update_model_config(
        model_config_id: str,
        payload: ModelConfigUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).update_model_config(
                tenant_id=tenant_id,
                model_config_id=model_config_id,
                payload=payload,
            )
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/tool-model-bindings")
    def list_tool_model_bindings(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        del admin
        return ModelConfigService(db).list_tool_model_bindings(tenant_id=tenant_id)

    @app.post(f"{settings.api_prefix}/admin/tool-model-bindings", status_code=status.HTTP_201_CREATED)
    def create_tool_model_binding(
        payload: ToolModelBindingCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).create_tool_model_binding(tenant_id=tenant_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put(f"{settings.api_prefix}/admin/tool-model-bindings/{{binding_id}}")
    def update_tool_model_binding(
        binding_id: str,
        payload: ToolModelBindingUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return ModelConfigService(db).update_tool_model_binding(tenant_id=tenant_id, binding_id=binding_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/workbench-capabilities")
    def admin_workbench_capabilities(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        return WorkbenchCapabilityService(db).list_capabilities(tenant_id=tenant_id, surface="workbench")

    @app.patch(f"{settings.api_prefix}/admin/workbench-capabilities")
    def update_workbench_capability(
        payload: WorkbenchCapabilityUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "OPERATOR")
        try:
            return WorkbenchCapabilityService(db).update_capability(tenant_id=tenant_id, payload=payload)
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/admin/home-slides")
    def list_home_slides(
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        del admin
        slides = HomeDashboardService(db).list_home_slides(tenant_id=tenant_id, include_disabled=True)
        return {"tenant_id": tenant_id, "slides": slides}

    @app.post(f"{settings.api_prefix}/admin/home-slides", status_code=status.HTTP_201_CREATED)
    def create_home_slide(
        payload: HomeHeroSlideCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        return HomeDashboardService(db).create_home_slide(tenant_id=tenant_id, payload=payload)

    @app.post(f"{settings.api_prefix}/admin/home-slides/reorder")
    def reorder_home_slides(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            slides = HomeDashboardService(db).reorder_home_slides(tenant_id=tenant_id, ordered_ids=payload.ordered_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"tenant_id": tenant_id, "slides": slides}

    @app.put(f"{settings.api_prefix}/admin/home-slides/{{slide_id}}")
    def update_home_slide(
        slide_id: str,
        payload: HomeHeroSlideUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            return HomeDashboardService(db).update_home_slide(tenant_id=tenant_id, slide_id=slide_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(f"{settings.api_prefix}/admin/home-slides/{{slide_id}}")
    def delete_home_slide(
        slide_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            return HomeDashboardService(db).disable_home_slide(tenant_id=tenant_id, slide_id=slide_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
        require_admin_role(admin, "CONTENT_EDITOR")
        page = AdminContentService(db).create_page(tenant_id=tenant_id, payload=payload)
        return PortalService._page_payload(page)

    @app.post(f"{settings.api_prefix}/admin/pages/reorder")
    def reorder_pages(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        require_admin_role(admin, "CONTENT_EDITOR")
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
        service = PortalService(db)
        return [service._item_payload(item) for item in AdminContentService(db).list_items(tenant_id=tenant_id, section_id=section_id)]

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
        return PortalService(db)._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/items", status_code=status.HTTP_201_CREATED)
    def create_item(
        payload: ContentItemCreate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            item = AdminContentService(db).create_content_item(tenant_id=tenant_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/items/reorder")
    def reorder_items(
        payload: ReorderRequest,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> list[dict]:
        require_admin_role(admin, "CONTENT_EDITOR")
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
        service = PortalService(db)
        return [service._item_payload(item) for item in items]

    @app.put(f"{settings.api_prefix}/admin/items/{{item_id}}")
    def update_item(
        item_id: str,
        payload: ContentItemUpdate,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            item = AdminContentService(db).update_content_item(tenant_id=tenant_id, item_id=item_id, payload=payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._item_payload(item)

    @app.delete(f"{settings.api_prefix}/admin/items/{{item_id}}")
    def delete_item(
        item_id: str,
        tenant_id: TenantHeader,
        db: Session = Depends(get_session),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
        try:
            item = AdminContentService(db).disable_content_item(tenant_id=tenant_id, item_id=item_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PortalService(db)._item_payload(item)

    @app.post(f"{settings.api_prefix}/admin/uploads", status_code=status.HTTP_201_CREATED)
    async def upload_image(
        tenant_id: TenantHeader,
        file: UploadFile = File(...),
        admin: User = Depends(require_admin),
    ) -> dict:
        require_admin_role(admin, "CONTENT_EDITOR")
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
        except ModelConfigError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RouteNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (InsufficientBalanceError, WalletNotFoundError) as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc
        except AudioProviderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get(f"{settings.api_prefix}/audio/tasks")
    def list_audio_tasks(
        tenant_id: TenantHeader,
        surface: GenerationSurface = "portal",
        db: Session = Depends(get_session),
    ) -> dict:
        return AudioService(db, app.state.audio_transport).list_tasks(tenant_id=tenant_id, surface=surface)

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
