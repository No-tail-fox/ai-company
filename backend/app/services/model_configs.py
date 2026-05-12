from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ApiChannel, ChannelRoute, ModelConfig, ToolModelBinding
from app.schemas import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ProviderChannelCreate,
    ProviderChannelUpdate,
    ToolModelBindingCreate,
    ToolModelBindingUpdate,
)


class ModelConfigError(ValueError):
    pass


class ModelBindingNotFoundError(ModelConfigError):
    pass


class ModelConfigNotAvailableError(ModelConfigError):
    pass


@dataclass(frozen=True)
class ResolvedModel:
    route_key: str
    provider_model: str
    effective_point_cost: int
    model_config: ModelConfig | None = None
    binding: ToolModelBinding | None = None
    channel: ApiChannel | None = None


class ModelConfigService:
    def __init__(self, session: Session):
        self.session = session

    def list_provider_channels(self, *, tenant_id: str) -> list[dict]:
        channels = list(
            self.session.scalars(
                select(ApiChannel)
                .where(ApiChannel.tenant_id == tenant_id)
                .order_by(ApiChannel.priority.asc(), ApiChannel.created_at.asc())
            )
        )
        return [self.provider_channel_payload(channel) for channel in channels]

    def create_provider_channel(self, *, tenant_id: str, payload: ProviderChannelCreate) -> dict:
        channel = ApiChannel(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(channel)
        self.session.commit()
        return self.provider_channel_payload(channel)

    def update_provider_channel(self, *, tenant_id: str, channel_id: str, payload: ProviderChannelUpdate) -> dict:
        channel = self._channel(tenant_id=tenant_id, channel_id=channel_id)
        for key, value in payload.model_dump(exclude_unset=True).items():
            if key == "api_key" and not value:
                continue
            setattr(channel, key, value)
        self.session.commit()
        return self.provider_channel_payload(channel)

    def list_model_configs(self, *, tenant_id: str) -> list[dict]:
        models = list(
            self.session.scalars(
                select(ModelConfig)
                .where(ModelConfig.tenant_id == tenant_id)
                .order_by(ModelConfig.capability.asc(), ModelConfig.created_at.asc())
            )
        )
        return [self.model_config_payload(model) for model in models]

    def create_model_config(self, *, tenant_id: str, payload: ModelConfigCreate) -> dict:
        self._channel(tenant_id=tenant_id, channel_id=payload.channel_id)
        model = ModelConfig(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(model)
        self.session.flush()
        self._sync_channel_route(model)
        self.session.commit()
        return self.model_config_payload(model)

    def update_model_config(self, *, tenant_id: str, model_config_id: str, payload: ModelConfigUpdate) -> dict:
        model = self._model(tenant_id=tenant_id, model_config_id=model_config_id)
        previous_key = model.model_key
        values = payload.model_dump(exclude_unset=True)
        if "channel_id" in values:
            self._channel(tenant_id=tenant_id, channel_id=values["channel_id"])
        for key, value in values.items():
            setattr(model, key, value)
        self._sync_channel_route(model, previous_model_key=previous_key)
        self.session.commit()
        return self.model_config_payload(model)

    def list_tool_model_bindings(self, *, tenant_id: str) -> list[dict]:
        bindings = list(
            self.session.scalars(
                select(ToolModelBinding)
                .where(ToolModelBinding.tenant_id == tenant_id)
                .order_by(ToolModelBinding.target_type.asc(), ToolModelBinding.target_key.asc())
            )
        )
        return [self.binding_payload(binding) for binding in bindings]

    def create_tool_model_binding(self, *, tenant_id: str, payload: ToolModelBindingCreate) -> dict:
        self._model(tenant_id=tenant_id, model_config_id=payload.model_config_id)
        binding = ToolModelBinding(tenant_id=tenant_id, **payload.model_dump())
        self.session.add(binding)
        self.session.commit()
        return self.binding_payload(binding)

    def update_tool_model_binding(self, *, tenant_id: str, binding_id: str, payload: ToolModelBindingUpdate) -> dict:
        binding = self._binding(tenant_id=tenant_id, binding_id=binding_id)
        values = payload.model_dump(exclude_unset=True)
        if "model_config_id" in values:
            self._model(tenant_id=tenant_id, model_config_id=values["model_config_id"])
        for key, value in values.items():
            setattr(binding, key, value)
        self.session.commit()
        return self.binding_payload(binding)

    def resolve_binding(
        self,
        *,
        tenant_id: str,
        target_type: str,
        target_key: str,
        require_enabled_channel: bool = True,
    ) -> ResolvedModel:
        binding = self.session.scalar(
            select(ToolModelBinding).where(
                ToolModelBinding.tenant_id == tenant_id,
                ToolModelBinding.target_type == target_type,
                ToolModelBinding.target_key == target_key,
                ToolModelBinding.enabled.is_(True),
            )
        )
        if binding is None:
            raise ModelBindingNotFoundError(f"model binding for {target_type}:{target_key} was not found")

        model = self._model(tenant_id=tenant_id, model_config_id=binding.model_config_id)
        if not model.enabled:
            raise ModelConfigNotAvailableError(f"model {model.model_key} is disabled")

        channel = self._channel(tenant_id=tenant_id, channel_id=model.channel_id)
        if require_enabled_channel and not channel.enabled:
            raise ModelConfigNotAvailableError(f"provider channel {channel.channel_key} is disabled")

        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == model.model_key,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise ModelConfigNotAvailableError(f"route for model {model.model_key} was not found or is disabled")

        return ResolvedModel(
            route_key=route.route_key,
            provider_model=model.provider_model,
            effective_point_cost=self.effective_point_cost(binding, model),
            model_config=model,
            binding=binding,
            channel=channel,
        )

    def resolve_generation_target(
        self,
        *,
        tenant_id: str,
        target_type: str | None,
        target_key: str | None,
        fallback_route_key: str,
    ) -> ResolvedModel:
        if target_type and target_key:
            return self.resolve_binding(
                tenant_id=tenant_id,
                target_type=target_type,
                target_key=target_key,
                require_enabled_channel=True,
            )

        route = self.session.scalar(
            select(ChannelRoute).where(
                ChannelRoute.tenant_id == tenant_id,
                ChannelRoute.route_key == fallback_route_key,
                ChannelRoute.enabled.is_(True),
            )
        )
        if route is None:
            raise ModelConfigNotAvailableError(f"route {fallback_route_key} was not found or is disabled")
        return ResolvedModel(route_key=route.route_key, provider_model=route.backend_model, effective_point_cost=route.unit_cost)

    def model_context_for_target(self, *, tenant_id: str, target_type: str, target_key: str) -> dict:
        binding = self.session.scalar(
            select(ToolModelBinding).where(
                ToolModelBinding.tenant_id == tenant_id,
                ToolModelBinding.target_type == target_type,
                ToolModelBinding.target_key == target_key,
                ToolModelBinding.enabled.is_(True),
            )
        )
        if binding is None:
            return {"model_config": None, "effective_point_cost": None}

        model = self._model(tenant_id=tenant_id, model_config_id=binding.model_config_id)
        if not model.enabled:
            return {"model_config": None, "effective_point_cost": None}

        channel = self._channel(tenant_id=tenant_id, channel_id=model.channel_id)
        if not channel.enabled:
            return {"model_config": None, "effective_point_cost": None}

        return {
            "model_config": self.model_config_payload(model),
            "effective_point_cost": self.effective_point_cost(binding, model),
        }

    def provider_channel_payload(self, channel: ApiChannel) -> dict:
        return {
            "id": channel.id,
            "tenant_id": channel.tenant_id,
            "channel_key": channel.channel_key,
            "display_name": channel.display_name,
            "base_url": channel.base_url,
            "api_key_mask": self.mask_api_key(channel.api_key),
            "channel_type": channel.channel_type,
            "adapter_type": channel.adapter_type,
            "priority": channel.priority,
            "enabled": channel.enabled,
            "health_status": channel.health_status,
            "timeout_seconds": channel.timeout_seconds,
            "metadata_json": channel.metadata_json or {},
        }

    def model_config_payload(self, model: ModelConfig | None) -> dict | None:
        if model is None:
            return None
        channel = self.session.get(ApiChannel, model.channel_id)
        return {
            "id": model.id,
            "tenant_id": model.tenant_id,
            "model_key": model.model_key,
            "display_name": model.display_name,
            "capability": model.capability,
            "channel_id": model.channel_id,
            "channel_key": channel.channel_key if channel else "",
            "channel_name": channel.display_name if channel else "",
            "provider_model": model.provider_model,
            "default_point_cost": model.default_point_cost,
            "enabled": model.enabled,
            "metadata_json": model.metadata_json or {},
        }

    def binding_payload(self, binding: ToolModelBinding) -> dict:
        model = self.session.get(ModelConfig, binding.model_config_id)
        return {
            "id": binding.id,
            "tenant_id": binding.tenant_id,
            "target_type": binding.target_type,
            "target_key": binding.target_key,
            "model_config_id": binding.model_config_id,
            "point_cost_override": binding.point_cost_override,
            "effective_point_cost": self.effective_point_cost(binding, model) if model else binding.point_cost_override,
            "enabled": binding.enabled,
            "model_config": self.model_config_payload(model),
        }

    def _sync_channel_route(self, model: ModelConfig, *, previous_model_key: str | None = None) -> ChannelRoute:
        lookup_keys = [key for key in [previous_model_key, model.model_key] if key]
        route = None
        for key in lookup_keys:
            route = self.session.scalar(
                select(ChannelRoute).where(
                    ChannelRoute.tenant_id == model.tenant_id,
                    ChannelRoute.route_key == key,
                )
            )
            if route is not None:
                break
        if route is None:
            route = ChannelRoute(
                tenant_id=model.tenant_id,
                route_key=model.model_key,
                display_name=model.display_name,
                backend_model=model.provider_model,
                channel_type=model.capability,
                unit_cost=model.default_point_cost,
                enabled=model.enabled,
            )
            self.session.add(route)
            return route

        route.route_key = model.model_key
        route.display_name = model.display_name
        route.backend_model = model.provider_model
        route.channel_type = model.capability
        route.unit_cost = model.default_point_cost
        route.enabled = model.enabled
        return route

    def _channel(self, *, tenant_id: str, channel_id: str) -> ApiChannel:
        channel = self.session.scalar(
            select(ApiChannel).where(
                ApiChannel.tenant_id == tenant_id,
                ApiChannel.id == channel_id,
            )
        )
        if channel is None:
            raise ModelConfigError("provider channel not found for tenant")
        return channel

    def _model(self, *, tenant_id: str, model_config_id: str) -> ModelConfig:
        model = self.session.scalar(
            select(ModelConfig).where(
                ModelConfig.tenant_id == tenant_id,
                ModelConfig.id == model_config_id,
            )
        )
        if model is None:
            raise ModelConfigNotAvailableError("model config not found for tenant")
        return model

    def _binding(self, *, tenant_id: str, binding_id: str) -> ToolModelBinding:
        binding = self.session.scalar(
            select(ToolModelBinding).where(
                ToolModelBinding.tenant_id == tenant_id,
                ToolModelBinding.id == binding_id,
            )
        )
        if binding is None:
            raise ModelBindingNotFoundError("tool model binding not found for tenant")
        return binding

    @staticmethod
    def effective_point_cost(binding: ToolModelBinding, model: ModelConfig | None) -> int:
        if binding.point_cost_override is not None:
            return binding.point_cost_override
        return model.default_point_cost if model else 0

    @staticmethod
    def mask_api_key(api_key: str | None) -> str:
        if not api_key:
            return ""
        suffix = api_key[-4:] if len(api_key) >= 4 else api_key
        return f"****{suffix}"
