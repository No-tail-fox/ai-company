from __future__ import annotations

from sqlalchemy import and_, or_


GENERATION_SURFACES = ("portal", "workbench")
DEFAULT_GENERATION_SURFACE = "portal"


def normalize_generation_surface(surface: str | None) -> str:
    if surface in GENERATION_SURFACES:
        return surface
    return DEFAULT_GENERATION_SURFACE


def namespace_request_key(surface: str | None, request_key: str) -> str:
    normalized = normalize_generation_surface(surface)
    if request_key.startswith(f"{normalized}:"):
        return request_key
    return f"{normalized}:{request_key}"


def surface_from_request_key(request_key: str | None) -> str:
    if request_key:
        for surface in GENERATION_SURFACES:
            if request_key.startswith(f"{surface}:"):
                return surface
    return DEFAULT_GENERATION_SURFACE


def surface_clause(request_key_column, surface: str | None):
    normalized = normalize_generation_surface(surface)
    if normalized != DEFAULT_GENERATION_SURFACE:
        return request_key_column.like(f"{normalized}:%")

    legacy_clause = and_(
        *[~request_key_column.like(f"{candidate}:%") for candidate in GENERATION_SURFACES]
    )
    return or_(request_key_column.like(f"{DEFAULT_GENERATION_SURFACE}:%"), legacy_clause)
