from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, Wallet
from app.services.memberships import MembershipService


class AccountNotFoundError(Exception):
    pass


class AccountService:
    def __init__(self, session: Session):
        self.session = session

    def summary(self, *, tenant_id: str, user_id: str) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=user_id)
        wallet = self._wallet(tenant_id=tenant_id, user_id=user_id)
        return {
            "user": self.user_payload(user),
            "wallet": {
                "balance": wallet.balance,
                "frozen_balance": wallet.frozen_balance,
                "currency": wallet.currency,
            },
            "membership": MembershipService(self.session).get_status(tenant_id=tenant_id, user_id=user_id),
        }

    def update_profile(self, *, tenant_id: str, user_id: str, display_name: str) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=user_id)
        user.display_name = display_name.strip()
        self.session.commit()
        self.session.refresh(user)
        return self.user_payload(user)

    def _user(self, *, tenant_id: str, user_id: str) -> User:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.id == user_id,
            )
        )
        if user is None:
            raise AccountNotFoundError(f"user {user_id} was not found")
        return user

    def _wallet(self, *, tenant_id: str, user_id: str) -> Wallet:
        wallet = self.session.scalar(
            select(Wallet).where(
                Wallet.tenant_id == tenant_id,
                Wallet.user_id == user_id,
            )
        )
        if wallet is None:
            raise AccountNotFoundError(f"wallet for user {user_id} was not found")
        return wallet

    @staticmethod
    def user_payload(user: User) -> dict:
        return {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "phone": user.phone,
            "display_name": user.display_name,
            "role": user.role,
            "status": user.status,
        }
