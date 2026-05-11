from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    MembershipPlan,
    RedemptionBatch,
    RedemptionCode,
    User,
    UserMembership,
    Wallet,
    WalletTransaction,
    utcnow,
)
from app.schemas import RedemptionBatchCreate
from app.services.account import AccountService
from app.services.memberships import MembershipService


class RedemptionError(Exception):
    pass


class RedemptionNotFoundError(RedemptionError):
    pass


class RedemptionValidationError(RedemptionError):
    pass


class RedemptionService:
    def __init__(self, session: Session):
        self.session = session

    def create_batch(self, *, tenant_id: str, payload: RedemptionBatchCreate, actor: User) -> dict:
        if payload.points <= 0 and not payload.membership_plan_id:
            raise RedemptionValidationError("redemption batch must grant points or membership")
        plan = None
        if payload.membership_plan_id:
            plan = self._plan(tenant_id=tenant_id, plan_id=payload.membership_plan_id)
            if not plan.enabled:
                raise RedemptionValidationError("membership plan is disabled")

        batch = RedemptionBatch(
            tenant_id=tenant_id,
            name=payload.name.strip(),
            points=payload.points,
            membership_plan_id=plan.id if plan else None,
            membership_days=payload.membership_days,
            quantity=payload.quantity,
            expires_at=self._parse_datetime(payload.expires_at) if payload.expires_at else None,
            created_by_user_id=actor.id,
        )
        self.session.add(batch)
        self.session.flush()

        generated_codes = []
        for _ in range(payload.quantity):
            plain_code = self._generate_unique_code(tenant_id=tenant_id)
            code = RedemptionCode(
                tenant_id=tenant_id,
                batch_id=batch.id,
                code_hash=self.hash_code(plain_code),
                code_suffix=self._code_suffix(plain_code),
            )
            self.session.add(code)
            self.session.flush()
            generated_codes.append(self.code_payload(code, code=plain_code))

        self.session.commit()
        self.session.refresh(batch)
        return {"batch": self.batch_payload(batch), "codes": generated_codes}

    def list_batches(self, *, tenant_id: str, limit: int = 100) -> list[dict]:
        batches = list(
            self.session.scalars(
                select(RedemptionBatch)
                .where(RedemptionBatch.tenant_id == tenant_id)
                .order_by(RedemptionBatch.created_at.desc())
                .limit(limit)
            )
        )
        return [self.batch_payload(batch) for batch in batches]

    def list_codes(self, *, tenant_id: str, batch_id: str | None = None, limit: int = 200) -> list[dict]:
        stmt = select(RedemptionCode).where(RedemptionCode.tenant_id == tenant_id)
        if batch_id:
            stmt = stmt.where(RedemptionCode.batch_id == batch_id)
        stmt = stmt.order_by(RedemptionCode.created_at.desc()).limit(limit)
        return [self.code_payload(code) for code in self.session.scalars(stmt)]

    def disable_code(self, *, tenant_id: str, code_id: str) -> dict:
        code = self._code_by_id(tenant_id=tenant_id, code_id=code_id)
        code.status = "DISABLED"
        self.session.commit()
        self.session.refresh(code)
        return self.code_payload(code)

    def redeem(self, *, tenant_id: str, user: User, code: str) -> dict:
        normalized_hash = self.hash_code(code)
        row = self.session.execute(
            select(RedemptionCode, RedemptionBatch)
            .join(RedemptionBatch, RedemptionBatch.id == RedemptionCode.batch_id)
            .where(
                RedemptionCode.tenant_id == tenant_id,
                RedemptionCode.code_hash == normalized_hash,
            )
        ).first()
        if row is None:
            raise RedemptionNotFoundError("redemption code was not found")
        redemption_code, batch = row
        if redemption_code.status != "ACTIVE":
            raise RedemptionValidationError("redemption code is not active")
        if batch.status != "ACTIVE":
            raise RedemptionValidationError("redemption batch is not active")
        now = utcnow()
        if batch.expires_at and batch.expires_at <= now:
            redemption_code.status = "EXPIRED"
            self.session.commit()
            raise RedemptionValidationError("redemption code is expired")

        wallet = self._wallet(tenant_id=tenant_id, user_id=user.id)
        if batch.points > 0:
            wallet.balance += batch.points
            self.session.add(
                WalletTransaction(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    wallet_id=wallet.id,
                    request_key=f"redemption:{redemption_code.id}",
                    amount=batch.points,
                    balance_after=wallet.balance,
                    type="RECHARGE",
                    remark=f"Redeemed {batch.name}",
                    related_ref=redemption_code.id,
                )
            )

        if batch.membership_plan_id:
            plan = self._plan(tenant_id=tenant_id, plan_id=batch.membership_plan_id)
            duration_days = batch.membership_days or plan.duration_days
            self._grant_or_extend_membership(
                tenant_id=tenant_id,
                user_id=user.id,
                plan_id=plan.id,
                duration_days=max(duration_days, 1),
                now=now,
            )

        redemption_code.status = "REDEEMED"
        redemption_code.redeemed_by_user_id = user.id
        redemption_code.redeemed_at = now
        self.session.commit()
        self.session.refresh(wallet)
        membership = MembershipService(self.session).get_status(tenant_id=tenant_id, user_id=user.id)
        account_summary = AccountService(self.session).summary(tenant_id=tenant_id, user_id=user.id)
        return {
            "status": "REDEEMED",
            "points_granted": batch.points,
            "membership": membership,
            "wallet": {
                "balance": wallet.balance,
                "frozen_balance": wallet.frozen_balance,
                "currency": wallet.currency,
            },
            "account_summary": account_summary,
        }

    def batch_payload(self, batch: RedemptionBatch) -> dict:
        generated_count = int(
            self.session.scalar(
                select(func.count(RedemptionCode.id)).where(
                    RedemptionCode.tenant_id == batch.tenant_id,
                    RedemptionCode.batch_id == batch.id,
                )
            )
            or 0
        )
        redeemed_count = int(
            self.session.scalar(
                select(func.count(RedemptionCode.id)).where(
                    RedemptionCode.tenant_id == batch.tenant_id,
                    RedemptionCode.batch_id == batch.id,
                    RedemptionCode.status == "REDEEMED",
                )
            )
            or 0
        )
        return {
            "id": batch.id,
            "tenant_id": batch.tenant_id,
            "name": batch.name,
            "points": batch.points,
            "membership_plan_id": batch.membership_plan_id,
            "membership_days": batch.membership_days,
            "quantity": batch.quantity,
            "status": batch.status,
            "expires_at": batch.expires_at.isoformat() if batch.expires_at else None,
            "generated_count": generated_count,
            "redeemed_count": redeemed_count,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "updated_at": batch.updated_at.isoformat() if batch.updated_at else None,
        }

    @staticmethod
    def code_payload(redemption_code: RedemptionCode, *, code: str | None = None) -> dict:
        payload = {
            "id": redemption_code.id,
            "tenant_id": redemption_code.tenant_id,
            "batch_id": redemption_code.batch_id,
            "masked_code": f"****{redemption_code.code_suffix}",
            "status": redemption_code.status,
            "redeemed_by_user_id": redemption_code.redeemed_by_user_id,
            "redeemed_at": redemption_code.redeemed_at.isoformat() if redemption_code.redeemed_at else None,
            "created_at": redemption_code.created_at.isoformat() if redemption_code.created_at else None,
        }
        if code is not None:
            payload["code"] = code
        return payload

    @classmethod
    def hash_code(cls, code: str) -> str:
        return hashlib.sha256(cls.normalize_code(code).encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_code(code: str) -> str:
        return code.strip().replace(" ", "").upper()

    def _generate_unique_code(self, *, tenant_id: str) -> str:
        for _ in range(20):
            raw = secrets.token_hex(8).upper()
            plain = f"RDM-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"
            existing = self.session.scalar(
                select(RedemptionCode.id).where(
                    RedemptionCode.tenant_id == tenant_id,
                    RedemptionCode.code_hash == self.hash_code(plain),
                )
            )
            if existing is None:
                return plain
        raise RedemptionValidationError("could not generate a unique redemption code")

    @staticmethod
    def _code_suffix(code: str) -> str:
        return RedemptionService.normalize_code(code)[-6:]

    def _wallet(self, *, tenant_id: str, user_id: str) -> Wallet:
        wallet = self.session.scalar(select(Wallet).where(Wallet.tenant_id == tenant_id, Wallet.user_id == user_id))
        if wallet is None:
            wallet = Wallet(tenant_id=tenant_id, user_id=user_id, balance=0, frozen_balance=0)
            self.session.add(wallet)
            self.session.flush()
        return wallet

    def _plan(self, *, tenant_id: str, plan_id: str) -> MembershipPlan:
        plan = self.session.scalar(
            select(MembershipPlan).where(MembershipPlan.tenant_id == tenant_id, MembershipPlan.id == plan_id)
        )
        if plan is None:
            raise RedemptionValidationError(f"membership plan {plan_id} was not found")
        return plan

    def _code_by_id(self, *, tenant_id: str, code_id: str) -> RedemptionCode:
        code = self.session.scalar(
            select(RedemptionCode).where(RedemptionCode.tenant_id == tenant_id, RedemptionCode.id == code_id)
        )
        if code is None:
            raise RedemptionNotFoundError(f"redemption code {code_id} was not found")
        return code

    def _grant_or_extend_membership(
        self,
        *,
        tenant_id: str,
        user_id: str,
        plan_id: str,
        duration_days: int,
        now: datetime,
    ) -> UserMembership:
        membership = self.session.scalar(
            select(UserMembership)
            .where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.user_id == user_id,
                UserMembership.plan_id == plan_id,
                UserMembership.status == "ACTIVE",
                UserMembership.expires_at > now,
            )
            .order_by(UserMembership.expires_at.desc())
        )
        if membership is not None:
            membership.expires_at = membership.expires_at + timedelta(days=duration_days)
            return membership
        membership = UserMembership(
            tenant_id=tenant_id,
            user_id=user_id,
            plan_id=plan_id,
            status="ACTIVE",
            started_at=now,
            expires_at=now + timedelta(days=duration_days),
        )
        self.session.add(membership)
        return membership

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
