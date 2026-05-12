from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiChannel, ContentItem, ContentSection, ModelConfig, ToolModelBinding
from app.schemas import WorkbenchCapabilityUpdate
from app.services.model_configs import ModelConfigError, ModelConfigService


CAPABILITY_GROUPS = ("chat", "image", "video", "audio")
AREA_TO_GROUP = {
    "workbench": "chat",
    "image": "image",
    "video": "video",
    "audio": "audio",
}


class WorkbenchCapabilityService:
    def __init__(self, session: Session):
        self.session = session
        self.model_configs = ModelConfigService(session)

    def list_capabilities(self, *, tenant_id: str, surface: str = "workbench", include_disabled: bool = True) -> dict:
        del surface
        capabilities = [self._capability_payload(item, section) for item, section in self._items(tenant_id=tenant_id)]
        if not include_disabled:
            capabilities = [capability for capability in capabilities if capability["enabled"]]
        groups = {group: [] for group in CAPABILITY_GROUPS}
        for capability in capabilities:
            groups.setdefault(capability["group"], []).append(capability)
        return {
            "tenant_id": tenant_id,
            "surface": "workbench",
            "capabilities": capabilities,
            "groups": groups,
        }

    def update_capability(self, *, tenant_id: str, payload: WorkbenchCapabilityUpdate) -> dict:
        binding = self.session.scalar(
            select(ToolModelBinding).where(
                ToolModelBinding.tenant_id == tenant_id,
                ToolModelBinding.target_type == payload.target_type,
                ToolModelBinding.target_key == payload.target_key,
            )
        )
        if binding is None:
            if not payload.model_config_id:
                raise ModelConfigError("model_config_id is required for new capability binding")
            self.model_configs._model(tenant_id=tenant_id, model_config_id=payload.model_config_id)
            binding = ToolModelBinding(
                tenant_id=tenant_id,
                target_type=payload.target_type,
                target_key=payload.target_key,
                model_config_id=payload.model_config_id,
                point_cost_override=payload.point_cost_override,
                enabled=payload.enabled if payload.enabled is not None else True,
            )
            self.session.add(binding)
        else:
            if payload.model_config_id:
                self.model_configs._model(tenant_id=tenant_id, model_config_id=payload.model_config_id)
                binding.model_config_id = payload.model_config_id
            if "point_cost_override" in payload.model_fields_set:
                binding.point_cost_override = payload.point_cost_override
            if payload.enabled is not None:
                binding.enabled = payload.enabled
        self.session.commit()
        return self.model_configs.binding_payload(binding)

    def _items(self, *, tenant_id: str) -> list[tuple[ContentItem, ContentSection]]:
        rows = self.session.execute(
            select(ContentItem, ContentSection)
            .join(ContentSection, ContentSection.id == ContentItem.section_id)
            .where(
                ContentItem.tenant_id == tenant_id,
                ContentSection.tenant_id == tenant_id,
                ContentItem.action_type.in_(["workspace", "route"]),
                ContentSection.area.in_(list(AREA_TO_GROUP.keys())),
            )
            .order_by(ContentSection.sort_order.asc(), ContentItem.sort_order.asc(), ContentItem.created_at.asc())
        )
        return [(item, section) for item, section in rows]

    def _capability_payload(self, item: ContentItem, section: ContentSection) -> dict:
        target_type = "content_item"
        target_key = item.id
        binding = self.session.scalar(
            select(ToolModelBinding).where(
                ToolModelBinding.tenant_id == item.tenant_id,
                ToolModelBinding.target_type == target_type,
                ToolModelBinding.target_key == target_key,
            )
        )
        binding_payload = self.model_configs.binding_payload(binding) if binding is not None else None
        model_payload = binding_payload["model_config"] if binding_payload else None
        unavailable_reason = self._unavailable_reason(item=item, binding=binding, model_payload=model_payload)
        enabled = item.enabled and section.enabled and (binding.enabled if binding else False)
        return {
            "id": item.id,
            "group": AREA_TO_GROUP.get(section.area, "chat"),
            "target_type": target_type,
            "target_key": target_key,
            "title": item.title,
            "subtitle": item.subtitle,
            "category": item.category,
            "icon": item.icon,
            "action_type": item.action_type,
            "action_value": item.action_value,
            "sort_order": item.sort_order,
            "enabled": enabled,
            "callable": enabled and not unavailable_reason,
            "unavailable_reason": unavailable_reason,
            "required_membership": item.required_membership,
            "effective_point_cost": binding_payload["effective_point_cost"] if binding_payload else item.point_cost,
            "model_config": model_payload,
        }

    def _unavailable_reason(
        self,
        *,
        item: ContentItem,
        binding: ToolModelBinding | None,
        model_payload: dict | None,
    ) -> str:
        if not item.enabled:
            return "capability disabled"
        if binding is None:
            return "model binding missing"
        if not binding.enabled:
            return "capability disabled"
        if model_payload is None:
            return "model disabled"
        model = self.session.get(ModelConfig, binding.model_config_id)
        if model is None or not model.enabled:
            return "model disabled"
        channel = self.session.get(ApiChannel, model.channel_id)
        if channel is None:
            return "provider channel missing"
        if not channel.enabled:
            return "provider channel disabled"
        return ""

