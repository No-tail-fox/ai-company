from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str
    password: str


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
