from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.settings import get_settings


HASH_NAME = "pbkdf2_sha256"
ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()
    return f"{HASH_NAME}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        name, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False
    if name != HASH_NAME:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)).hex()
    return hmac.compare_digest(digest, expected)


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def authenticate(self, *, tenant_id: str, phone: str, password: str) -> User | None:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.phone == phone,
                User.status == "ACTIVE",
            )
        )
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        settings = get_settings()
        now = datetime.now(UTC)
        payload = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def user_from_token(self, *, tenant_id: str, token: str) -> User | None:
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        except jwt.PyJWTError:
            return None
        if payload.get("tenant_id") != tenant_id:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return self.session.scalar(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.status == "ACTIVE",
            )
        )
