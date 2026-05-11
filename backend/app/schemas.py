from typing import Literal

from pydantic import BaseModel, Field


GenerationSurface = Literal["portal", "workbench"]


class LoginRequest(BaseModel):
    phone: str
    password: str


class AccountProfileUpdate(BaseModel):
    user_id: str = "demo-user"
    display_name: str = Field(min_length=1, max_length=64)


class RechargeOrderCreate(BaseModel):
    user_id: str = "demo-user"
    package_key: str


class AdminUserCreate(BaseModel):
    phone: str
    display_name: str
    role: str = "USER"
    status: str = "ACTIVE"
    password: str = ""


class AdminUserUpdate(BaseModel):
    phone: str | None = None
    display_name: str | None = None
    role: str | None = None
    status: str | None = None
    password: str | None = None


class WalletAdjustmentCreate(BaseModel):
    amount: int
    reason: str = ""
    request_key: str | None = None


class MembershipPlanCreate(BaseModel):
    plan_key: str
    name: str
    price_cents: int = 0
    duration_days: int = 31
    entitlements: list[str] = Field(default_factory=list)
    enabled: bool = True
    sort_order: int = 100


class MembershipPlanUpdate(BaseModel):
    plan_key: str | None = None
    name: str | None = None
    price_cents: int | None = None
    duration_days: int | None = None
    entitlements: list[str] | None = None
    enabled: bool | None = None
    sort_order: int | None = None


class UserMembershipCreate(BaseModel):
    user_id: str
    plan_id: str
    duration_days: int | None = None
    status: str = "ACTIVE"


class UserMembershipUpdate(BaseModel):
    plan_id: str | None = None
    status: str | None = None
    expires_at: str | None = None


class ContentPageCreate(BaseModel):
    page_key: str
    label: str
    title: str
    subtitle: str = ""
    icon: str = "Sparkles"
    sort_order: int = 100
    enabled: bool = True


class ContentPageUpdate(BaseModel):
    label: str | None = None
    title: str | None = None
    subtitle: str | None = None
    icon: str | None = None
    sort_order: int | None = None
    enabled: bool | None = None


class ContentSectionCreate(BaseModel):
    page_key: str
    section_key: str
    title: str
    subtitle: str = ""
    layout: str = "grid"
    sort_order: int = 100
    enabled: bool = True


class ContentSectionUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    layout: str | None = None
    sort_order: int | None = None
    enabled: bool | None = None


class ReorderRequest(BaseModel):
    ordered_ids: list[str]
    section_id: str | None = None


class ContentItemCreate(BaseModel):
    section_id: str
    item_type: str
    title: str
    subtitle: str = ""
    category: str = ""
    icon: str = ""
    image_url: str = ""
    badge: str = ""
    tags: list[str] = Field(default_factory=list)
    sort_order: int = 100
    enabled: bool = True
    action_type: str = "route"
    action_value: str = ""
    required_membership: bool = False
    point_cost: int = 0
    metadata_json: dict | None = None


class ContentItemUpdate(BaseModel):
    item_type: str | None = None
    title: str | None = None
    subtitle: str | None = None
    category: str | None = None
    icon: str | None = None
    image_url: str | None = None
    badge: str | None = None
    tags: list[str] | None = None
    sort_order: int | None = None
    enabled: bool | None = None
    action_type: str | None = None
    action_value: str | None = None
    required_membership: bool | None = None
    point_cost: int | None = None
    metadata_json: dict | None = None


class HomeHeroSlideCreate(BaseModel):
    title: str
    subtitle: str = ""
    badge: str = ""
    cta_label: str = "立即查看"
    cta_subtitle: str = ""
    image_url: str = ""
    action_type: str = "route"
    action_value: str = ""
    sort_order: int = 100
    enabled: bool = True
    metadata_json: dict | None = None


class HomeHeroSlideUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    badge: str | None = None
    cta_label: str | None = None
    cta_subtitle: str | None = None
    image_url: str | None = None
    action_type: str | None = None
    action_value: str | None = None
    sort_order: int | None = None
    enabled: bool | None = None
    metadata_json: dict | None = None


class AudioTaskCreate(BaseModel):
    task_type: str
    route_key: str
    prompt: str
    source_url: str = ""
    voice_key: str = ""
    target_type: str | None = None
    target_id: str | None = None
    request_key: str | None = None
    surface: GenerationSurface = "portal"


class VideoGenerationCreate(BaseModel):
    prompt: str
    user_id: str = "demo-user"
    route_key: str = "video_text_to_video"
    request_key: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    surface: GenerationSurface = "portal"


class VideoWalletPayload(BaseModel):
    balance: int
    frozen_balance: int


class VideoRoutePayload(BaseModel):
    route_key: str
    unit_cost: int


class VideoTaskPayload(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    surface: GenerationSurface = "portal"
    task_type: str
    route_key: str
    prompt: str
    status: str
    estimated_cost: int
    actual_cost: int | None = None
    provider_task_id: str | None = None
    result_url: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class VideoWorkbenchPayload(BaseModel):
    tenant_id: str
    user_id: str
    surface: GenerationSurface = "portal"
    wallet: VideoWalletPayload
    route: VideoRoutePayload
    tasks: list[VideoTaskPayload]


class ImageGenerationCreate(BaseModel):
    prompt: str
    user_id: str = "demo-user"
    route_key: str = "image_text_to_image"
    request_key: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    surface: GenerationSurface = "portal"


class ImageWalletPayload(BaseModel):
    balance: int
    frozen_balance: int


class ImageRoutePayload(BaseModel):
    route_key: str
    unit_cost: int


class ImageTaskPayload(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    surface: GenerationSurface = "portal"
    task_type: str
    route_key: str
    prompt: str
    status: str
    estimated_cost: int
    actual_cost: int | None = None
    provider_task_id: str | None = None
    result_url: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ImageWorkbenchPayload(BaseModel):
    tenant_id: str
    user_id: str
    surface: GenerationSurface = "portal"
    wallet: ImageWalletPayload
    route: ImageRoutePayload
    tasks: list[ImageTaskPayload]


class ChatSessionCreate(BaseModel):
    title: str = ""
    user_id: str = "demo-user"
    model_key: str = "general_text_default"
    preset_role: str = "assistant"


class ChatSessionUpdate(BaseModel):
    title: str | None = None
    model_key: str | None = None
    preset_role: str | None = None
    status: str | None = None


class ChatMessageCreate(BaseModel):
    content: str
    model_key: str | None = None


class ChatExportCreate(BaseModel):
    format: str = "markdown"


class PortalActionCreate(BaseModel):
    user_id: str = "demo-user"
    detail_path: str
    item_id: str | None = None
    action_key: str


class AssistantCreate(BaseModel):
    assistant_key: str
    name: str
    description: str = ""
    category: str = ""
    icon: str = "Bot"
    usage_count: int = 0
    sort_order: int = 100
    enabled: bool = True
    action_type: str = "workspace"
    action_value: str = ""
    required_membership: bool = False
    point_cost: int = 0


class ProviderChannelCreate(BaseModel):
    channel_key: str
    display_name: str
    base_url: str
    api_key: str = ""
    channel_type: str
    priority: int = 100
    enabled: bool = True
    timeout_seconds: int = 60


class ProviderChannelUpdate(BaseModel):
    channel_key: str | None = None
    display_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    channel_type: str | None = None
    priority: int | None = None
    enabled: bool | None = None
    timeout_seconds: int | None = None


class ModelConfigCreate(BaseModel):
    model_key: str
    display_name: str
    capability: str
    channel_id: str
    provider_model: str
    default_point_cost: int = 0
    enabled: bool = True


class ModelConfigUpdate(BaseModel):
    model_key: str | None = None
    display_name: str | None = None
    capability: str | None = None
    channel_id: str | None = None
    provider_model: str | None = None
    default_point_cost: int | None = None
    enabled: bool | None = None


class ToolModelBindingCreate(BaseModel):
    target_type: str
    target_key: str
    model_config_id: str
    point_cost_override: int | None = None
    enabled: bool = True


class ToolModelBindingUpdate(BaseModel):
    target_type: str | None = None
    target_key: str | None = None
    model_config_id: str | None = None
    point_cost_override: int | None = None
    enabled: bool | None = None
