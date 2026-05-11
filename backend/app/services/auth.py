from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Wallet
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

    def create_verification_code(self, *, tenant_id: str, phone: str, purpose: str) -> dict:
        del tenant_id
        settings = get_settings()
        normalized_purpose = purpose.strip().upper()
        if normalized_purpose not in {"REGISTER", "LOGIN", "RESET_PASSWORD"}:
            raise ValueError("unsupported verification code purpose")
        return {
            "phone": phone.strip(),
            "purpose": normalized_purpose,
            "channel": "placeholder",
            "message": "verification code sending is configured as a placeholder",
            "dev_code": settings.otp_default_code,
        }

    def verify_code(self, *, phone: str, purpose: str, verification_code: str | None) -> bool:
        del phone, purpose
        settings = get_settings()
        return bool(verification_code) and hmac.compare_digest(verification_code.strip(), settings.otp_default_code)

    def register_user(self, *, tenant_id: str, phone: str, password: str, display_name: str, verification_code: str) -> User:
        phone = phone.strip()
        if not self.verify_code(phone=phone, purpose="REGISTER", verification_code=verification_code):
            raise ValueError("invalid verification code")
        existing = self.session.scalar(
            select(User.id).where(
                User.tenant_id == tenant_id,
                User.phone == phone,
            )
        )
        if existing is not None:
            raise ValueError("phone already registered")

        user = User(
            tenant_id=tenant_id,
            phone=phone,
            display_name=display_name.strip(),
            role="USER",
            status="ACTIVE",
            password_hash=hash_password(password),
        )
        self.session.add(user)
        self.session.flush()
        self.session.add(Wallet(tenant_id=tenant_id, user_id=user.id, balance=0, frozen_balance=0))
        self.session.commit()
        self.session.refresh(user)
        return user

    def authenticate(self, *, tenant_id: str, phone: str, password: str) -> User | None:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.phone == phone.strip(),
                User.status == "ACTIVE",
            )
        )
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def reset_password(self, *, tenant_id: str, phone: str, verification_code: str, new_password: str) -> User:
        phone = phone.strip()
        if not self.verify_code(phone=phone, purpose="RESET_PASSWORD", verification_code=verification_code):
            raise ValueError("invalid verification code")
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.phone == phone,
                User.status == "ACTIVE",
            )
        )
        if user is None:
            raise ValueError("user was not found")
        user.password_hash = hash_password(new_password)
        self.session.commit()
        self.session.refresh(user)
        return user

    def change_password(self, *, user: User, current_password: str, new_password: str) -> User:
        if not verify_password(current_password, user.password_hash):
            raise ValueError("current password is invalid")
        user.password_hash = hash_password(new_password)
        self.session.commit()
        self.session.refresh(user)
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
