from __future__ import annotations


ROLE_RANKS = {
    "READ_ONLY": 10,
    "CONTENT_EDITOR": 20,
    "OPERATOR": 30,
    "ADMIN": 40,
    "SUPER_ADMIN": 40,
}


def role_rank(role: str | None) -> int:
    return ROLE_RANKS.get(str(role or "").upper(), 0)


def is_admin_role(role: str | None) -> bool:
    return role_rank(role) >= ROLE_RANKS["READ_ONLY"]


def has_min_role(role: str | None, minimum_role: str) -> bool:
    return role_rank(role) >= role_rank(minimum_role)
