from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    AdminActionLog,
    ApiChannel,
    ContentItem,
    ContentPage,
    ContentSection,
    MembershipPlan,
    ModelConfig,
    ToolModelBinding,
    User,
    UserMembership,
    Wallet,
    WalletTransaction,
    utcnow,
    new_id,
)
from app.schemas import (
    AdminUserCreate,
    AdminUserUpdate,
    MembershipPlanCreate,
    MembershipPlanUpdate,
    UserMembershipCreate,
    UserMembershipUpdate,
    WalletAdjustmentCreate,
)
from app.services.auth import hash_password
from app.services.wallet import InsufficientBalanceError, WalletService


class AdminManagementService:
    def __init__(self, session: Session):
        self.session = session

    def overview(self, *, tenant_id: str) -> dict:
        wallet_totals = self.session.execute(
            select(
                func.coalesce(func.sum(Wallet.balance), 0),
                func.coalesce(func.sum(Wallet.frozen_balance), 0),
            ).where(Wallet.tenant_id == tenant_id)
        ).one()
        return {
            "tenant_id": tenant_id,
            "users": {
                "total": self._count(User, tenant_id),
                "active": self._count(User, tenant_id, User.status == "ACTIVE"),
                "admins": self._count(User, tenant_id, User.role.in_(["ADMIN", "SUPER_ADMIN"])),
            },
            "membership_plans": {
                "total": self._count(MembershipPlan, tenant_id),
                "enabled": self._count(MembershipPlan, tenant_id, MembershipPlan.enabled.is_(True)),
            },
            "wallets": {
                "total_balance": int(wallet_totals[0] or 0),
                "frozen_balance": int(wallet_totals[1] or 0),
            },
            "content": {
                "pages": self._count(ContentPage, tenant_id),
                "sections": self._count(ContentSection, tenant_id),
                "items": self._count(ContentItem, tenant_id),
            },
            "models": {
                "channels": self._count(ApiChannel, tenant_id),
                "model_configs": self._count(ModelConfig, tenant_id),
                "bindings": self._count(ToolModelBinding, tenant_id),
            },
            "recent_logs": [self.audit_log_payload(log) for log in self.list_audit_logs(tenant_id=tenant_id, limit=5)],
        }

    def list_users(
        self,
        *,
        tenant_id: str,
        query: str = "",
        role: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        stmt = select(User).where(User.tenant_id == tenant_id)
        if query:
            like = f"%{query.strip()}%"
            stmt = stmt.where(or_(User.phone.like(like), User.display_name.like(like)))
        if role:
            stmt = stmt.where(User.role == role)
        if status:
            stmt = stmt.where(User.status == status)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit)
        users = list(self.session.scalars(stmt))
        active_memberships = self._active_memberships_by_user(tenant_id=tenant_id)
        wallets = {
            wallet.user_id: wallet
            for wallet in self.session.scalars(select(Wallet).where(Wallet.tenant_id == tenant_id))
        }
        return [
            self.user_payload(
                user,
                wallet=wallets.get(user.id),
                membership=active_memberships.get(user.id),
            )
            for user in users
        ]

    def create_user(self, *, tenant_id: str, payload: AdminUserCreate, actor: User) -> dict:
        self._ensure_unique_phone(tenant_id=tenant_id, phone=payload.phone)
        user = User(
            tenant_id=tenant_id,
            phone=payload.phone.strip(),
            display_name=payload.display_name.strip(),
            role=payload.role.strip().upper() or "USER",
            status=payload.status.strip().upper() or "ACTIVE",
            password_hash=hash_password(payload.password) if payload.password else None,
        )
        self.session.add(user)
        self.session.flush()
        self._ensure_wallet(tenant_id=tenant_id, user=user)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="user.create",
            target_type="user",
            target_id=user.id,
            summary=f"创建用户 {user.display_name or user.phone}",
        )
        self.session.commit()
        self.session.refresh(user)
        return self.user_payload(user, wallet=self._wallet_or_none(tenant_id=tenant_id, user_id=user.id))

    def update_user(self, *, tenant_id: str, user_id: str, payload: AdminUserUpdate, actor: User) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=user_id)
        values = payload.model_dump(exclude_unset=True)
        if "phone" in values and values["phone"] and values["phone"] != user.phone:
            self._ensure_unique_phone(tenant_id=tenant_id, phone=values["phone"], exclude_user_id=user.id)
        if "password" in values:
            password = values.pop("password")
            if password:
                user.password_hash = hash_password(password)
        for key, value in values.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(user, key, value.upper() if key in {"role", "status"} and value else value)
        self._ensure_wallet(tenant_id=tenant_id, user=user)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="user.update",
            target_type="user",
            target_id=user.id,
            summary=f"更新用户 {user.display_name or user.phone}",
        )
        self.session.commit()
        self.session.refresh(user)
        return self.user_payload(user, wallet=self._wallet_or_none(tenant_id=tenant_id, user_id=user.id))

    def disable_user(self, *, tenant_id: str, user_id: str, actor: User) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=user_id)
        user.status = "INACTIVE"
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="user.disable",
            target_type="user",
            target_id=user.id,
            summary=f"停用用户 {user.display_name or user.phone}",
        )
        self.session.commit()
        return self.user_payload(user, wallet=self._wallet_or_none(tenant_id=tenant_id, user_id=user.id))

    def list_wallet_transactions(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        stmt = select(WalletTransaction).where(WalletTransaction.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(WalletTransaction.user_id == user_id)
        stmt = stmt.order_by(WalletTransaction.created_at.desc()).limit(limit)
        transactions = list(self.session.scalars(stmt))
        return [self.wallet_transaction_payload(transaction) for transaction in transactions]

    def adjust_wallet(self, *, tenant_id: str, user_id: str, payload: WalletAdjustmentCreate, actor: User) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=user_id)
        request_key = payload.request_key or f"admin-wallet:{user_id}:{new_id()}"
        transaction = WalletService(self.session).adjust_balance(
            tenant_id=tenant_id,
            user_id=user_id,
            amount=payload.amount,
            reason=payload.reason or "管理员手工调整",
            request_key=request_key,
        )
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="wallet.adjust",
            target_type="wallet",
            target_id=user.id,
            summary=f"调整 {user.display_name or user.phone} 积分 {payload.amount:+d}",
        )
        self.session.commit()
        wallet = self._wallet_or_none(tenant_id=tenant_id, user_id=user_id)
        return {
            **self.wallet_payload(wallet),
            "transaction": self.wallet_transaction_payload(transaction),
        }

    def list_membership_plans(self, *, tenant_id: str) -> list[dict]:
        plans = list(
            self.session.scalars(
                select(MembershipPlan)
                .where(MembershipPlan.tenant_id == tenant_id)
                .order_by(MembershipPlan.sort_order.asc(), MembershipPlan.created_at.asc())
            )
        )
        active_counts = self._membership_plan_active_counts(tenant_id=tenant_id)
        return [self.membership_plan_payload(plan, active_count=active_counts.get(plan.id, 0)) for plan in plans]

    def create_membership_plan(self, *, tenant_id: str, payload: MembershipPlanCreate, actor: User) -> dict:
        self._ensure_unique_plan_key(tenant_id=tenant_id, plan_key=payload.plan_key)
        plan = MembershipPlan(
            tenant_id=tenant_id,
            plan_key=payload.plan_key.strip(),
            name=payload.name.strip(),
            price_cents=payload.price_cents,
            duration_days=payload.duration_days,
            entitlements=payload.entitlements,
            enabled=payload.enabled,
            sort_order=payload.sort_order,
        )
        self.session.add(plan)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership_plan.create",
            target_type="membership_plan",
            target_id="",
            summary=f"创建会员套餐 {plan.name}",
        )
        self.session.commit()
        self.session.refresh(plan)
        return self.membership_plan_payload(plan, active_count=0)

    def update_membership_plan(self, *, tenant_id: str, plan_id: str, payload: MembershipPlanUpdate, actor: User) -> dict:
        plan = self._plan(tenant_id=tenant_id, plan_id=plan_id)
        values = payload.model_dump(exclude_unset=True)
        if "plan_key" in values and values["plan_key"] and values["plan_key"] != plan.plan_key:
            self._ensure_unique_plan_key(tenant_id=tenant_id, plan_key=values["plan_key"], exclude_plan_id=plan.id)
        for key, value in values.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(plan, key, value)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership_plan.update",
            target_type="membership_plan",
            target_id=plan.id,
            summary=f"更新会员套餐 {plan.name}",
        )
        self.session.commit()
        return self.membership_plan_payload(plan, active_count=self._membership_plan_active_counts(tenant_id=tenant_id).get(plan.id, 0))

    def disable_membership_plan(self, *, tenant_id: str, plan_id: str, actor: User) -> dict:
        plan = self._plan(tenant_id=tenant_id, plan_id=plan_id)
        plan.enabled = False
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership_plan.disable",
            target_type="membership_plan",
            target_id=plan.id,
            summary=f"停用会员套餐 {plan.name}",
        )
        self.session.commit()
        return self.membership_plan_payload(plan, active_count=self._membership_plan_active_counts(tenant_id=tenant_id).get(plan.id, 0))

    def list_user_memberships(
        self,
        *,
        tenant_id: str,
        user_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        stmt = (
            select(UserMembership, User, MembershipPlan)
            .join(User, User.id == UserMembership.user_id)
            .join(MembershipPlan, MembershipPlan.id == UserMembership.plan_id)
            .where(UserMembership.tenant_id == tenant_id)
            .order_by(UserMembership.created_at.desc())
            .limit(limit)
        )
        if user_id:
            stmt = stmt.where(UserMembership.user_id == user_id)
        rows = self.session.execute(stmt).all()
        return [self.user_membership_payload(membership, user=user, plan=plan) for membership, user, plan in rows]

    def grant_membership(
        self,
        *,
        tenant_id: str,
        payload: UserMembershipCreate,
        actor: User,
    ) -> dict:
        user = self._user(tenant_id=tenant_id, user_id=payload.user_id)
        plan = self._plan(tenant_id=tenant_id, plan_id=payload.plan_id)
        started_at = utcnow()
        duration_days = payload.duration_days or plan.duration_days
        membership = UserMembership(
            tenant_id=tenant_id,
            user_id=user.id,
            plan_id=plan.id,
            status=payload.status.upper() if payload.status else "ACTIVE",
            started_at=started_at,
            expires_at=started_at + timedelta(days=max(duration_days, 1)),
        )
        self.session.add(membership)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership.grant",
            target_type="user_membership",
            target_id="",
            summary=f"为 {user.display_name or user.phone} 开通 {plan.name}",
        )
        self.session.commit()
        self.session.refresh(membership)
        return self.user_membership_payload(membership, user=user, plan=plan)

    def update_user_membership(
        self,
        *,
        tenant_id: str,
        membership_id: str,
        payload: UserMembershipUpdate,
        actor: User,
    ) -> dict:
        membership = self._user_membership(tenant_id=tenant_id, membership_id=membership_id)
        values = payload.model_dump(exclude_unset=True)
        if "plan_id" in values and values["plan_id"]:
            self._plan(tenant_id=tenant_id, plan_id=values["plan_id"])
        if "expires_at" in values and values["expires_at"]:
            values["expires_at"] = self._parse_datetime(values["expires_at"])
        for key, value in values.items():
            if isinstance(value, str) and key != "expires_at":
                value = value.strip()
            if key == "status" and value:
                value = value.upper()
            setattr(membership, key, value)
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership.update",
            target_type="user_membership",
            target_id=membership.id,
            summary=f"更新会员记录 {membership.id}",
        )
        self.session.commit()
        self.session.refresh(membership)
        return self.user_membership_payload(
            membership,
            user=self._user(tenant_id=tenant_id, user_id=membership.user_id),
            plan=self._plan(tenant_id=tenant_id, plan_id=membership.plan_id),
        )

    def disable_user_membership(self, *, tenant_id: str, membership_id: str, actor: User) -> dict:
        membership = self._user_membership(tenant_id=tenant_id, membership_id=membership_id)
        membership.status = "EXPIRED"
        self.record_audit(
            tenant_id=tenant_id,
            actor=actor,
            action="membership.disable",
            target_type="user_membership",
            target_id=membership.id,
            summary=f"停用会员记录 {membership.id}",
        )
        self.session.commit()
        return self.user_membership_payload(
            membership,
            user=self._user(tenant_id=tenant_id, user_id=membership.user_id),
            plan=self._plan(tenant_id=tenant_id, plan_id=membership.plan_id),
        )

    def list_audit_logs(self, *, tenant_id: str, limit: int = 50) -> list[AdminActionLog]:
        stmt = (
            select(AdminActionLog)
            .where(AdminActionLog.tenant_id == tenant_id)
            .order_by(AdminActionLog.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def record_audit(
        self,
        *,
        tenant_id: str,
        actor: User,
        action: str,
        target_type: str,
        target_id: str,
        summary: str,
    ) -> AdminActionLog:
        log = AdminActionLog(
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            actor_display_name=actor.display_name,
            actor_role=actor.role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=summary,
        )
        self.session.add(log)
        return log

    def user_payload(self, user: User, *, wallet: Wallet | None = None, membership: dict | None = None) -> dict:
        wallet = wallet or self._wallet_or_none(tenant_id=user.tenant_id, user_id=user.id)
        membership_plan = (membership or {}).get("plan") if membership else None
        membership_record = (membership or {}).get("membership") if membership else None
        return {
            "id": user.id,
            "tenant_id": user.tenant_id,
            "phone": user.phone,
            "display_name": user.display_name,
            "role": user.role,
            "status": user.status,
            "balance": wallet.balance if wallet else 0,
            "frozen_balance": wallet.frozen_balance if wallet else 0,
            "currency": wallet.currency if wallet else "POINT",
            "membership_plan_id": membership_plan.id if membership_plan else None,
            "membership_plan_key": membership_plan.plan_key if membership_plan else None,
            "membership_plan_name": membership_plan.name if membership_plan else None,
            "membership_status": membership_record.status if membership_record else None,
            "membership_expires_at": membership_record.expires_at.isoformat() if membership_record and membership_record.expires_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    def wallet_payload(self, wallet: Wallet | None) -> dict:
        if wallet is None:
            return {"balance": 0, "frozen_balance": 0, "currency": "POINT"}
        return {
            "balance": wallet.balance,
            "frozen_balance": wallet.frozen_balance,
            "currency": wallet.currency,
        }

    def wallet_transaction_payload(self, transaction: WalletTransaction) -> dict:
        user = self._user(tenant_id=transaction.tenant_id, user_id=transaction.user_id)
        return {
            "id": transaction.id,
            "tenant_id": transaction.tenant_id,
            "user_id": transaction.user_id,
            "user_display_name": user.display_name,
            "request_key": transaction.request_key,
            "amount": transaction.amount,
            "balance_after": transaction.balance_after,
            "type": transaction.type,
            "remark": transaction.remark,
            "related_ref": transaction.related_ref,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None,
        }

    def membership_plan_payload(self, plan: MembershipPlan, *, active_count: int = 0) -> dict:
        return {
            "id": plan.id,
            "tenant_id": plan.tenant_id,
            "plan_key": plan.plan_key,
            "name": plan.name,
            "price_cents": plan.price_cents,
            "duration_days": plan.duration_days,
            "entitlements": plan.entitlements or [],
            "enabled": plan.enabled,
            "sort_order": plan.sort_order,
            "active_user_count": active_count,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }

    def user_membership_payload(self, membership: UserMembership, *, user: User, plan: MembershipPlan) -> dict:
        return {
            "id": membership.id,
            "tenant_id": membership.tenant_id,
            "user_id": membership.user_id,
            "user_display_name": user.display_name,
            "user_phone": user.phone,
            "plan": self.membership_plan_payload(plan),
            "status": membership.status,
            "started_at": membership.started_at.isoformat() if membership.started_at else None,
            "expires_at": membership.expires_at.isoformat() if membership.expires_at else None,
            "created_at": membership.created_at.isoformat() if membership.created_at else None,
            "updated_at": membership.updated_at.isoformat() if membership.updated_at else None,
        }

    def audit_log_payload(self, log: AdminActionLog) -> dict:
        return {
            "id": log.id,
            "tenant_id": log.tenant_id,
            "actor_user_id": log.actor_user_id,
            "actor_display_name": log.actor_display_name,
            "actor_role": log.actor_role,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "summary": log.summary,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }

    def _active_memberships_by_user(self, *, tenant_id: str) -> dict[str, dict]:
        now = utcnow()
        rows = self.session.execute(
            select(UserMembership, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.id == UserMembership.plan_id)
            .where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.status == "ACTIVE",
                UserMembership.expires_at > now,
                MembershipPlan.enabled.is_(True),
            )
            .order_by(UserMembership.expires_at.desc())
        ).all()
        result: dict[str, dict] = {}
        for membership, plan in rows:
            if membership.user_id not in result:
                result[membership.user_id] = {"membership": membership, "plan": plan}
        return result

    def _membership_plan_active_counts(self, *, tenant_id: str) -> dict[str, int]:
        now = utcnow()
        rows = self.session.execute(
            select(UserMembership.plan_id, func.count(UserMembership.id))
            .where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.status == "ACTIVE",
                UserMembership.expires_at > now,
            )
            .group_by(UserMembership.plan_id)
        ).all()
        return {plan_id: int(count) for plan_id, count in rows}

    def _count(self, model, tenant_id: str, *criteria) -> int:
        stmt = select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
        for criterion in criteria:
            stmt = stmt.where(criterion)
        return int(self.session.scalar(stmt) or 0)

    def _user(self, *, tenant_id: str, user_id: str) -> User:
        user = self.session.scalar(
            select(User).where(
                User.tenant_id == tenant_id,
                User.id == user_id,
            )
        )
        if user is None:
            raise ValueError(f"user {user_id} was not found")
        return user

    def _wallet_or_none(self, *, tenant_id: str, user_id: str) -> Wallet | None:
        return self.session.scalar(
            select(Wallet).where(
                Wallet.tenant_id == tenant_id,
                Wallet.user_id == user_id,
            )
        )

    def _ensure_wallet(self, *, tenant_id: str, user: User) -> Wallet:
        wallet = self._wallet_or_none(tenant_id=tenant_id, user_id=user.id)
        if wallet is not None:
            return wallet
        wallet = Wallet(
            tenant_id=tenant_id,
            user_id=user.id,
            balance=0,
            frozen_balance=0,
        )
        self.session.add(wallet)
        self.session.flush()
        return wallet

    def _plan(self, *, tenant_id: str, plan_id: str) -> MembershipPlan:
        plan = self.session.scalar(
            select(MembershipPlan).where(
                MembershipPlan.tenant_id == tenant_id,
                MembershipPlan.id == plan_id,
            )
        )
        if plan is None:
            raise ValueError(f"membership plan {plan_id} was not found")
        return plan

    def _user_membership(self, *, tenant_id: str, membership_id: str) -> UserMembership:
        membership = self.session.scalar(
            select(UserMembership).where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.id == membership_id,
            )
        )
        if membership is None:
            raise ValueError(f"membership {membership_id} was not found")
        return membership

    def _ensure_unique_phone(self, *, tenant_id: str, phone: str, exclude_user_id: str | None = None) -> None:
        stmt = select(User.id).where(
            User.tenant_id == tenant_id,
            User.phone == phone.strip(),
        )
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)
        existing = self.session.scalar(stmt)
        if existing is not None:
            raise ValueError(f"user phone {phone} already exists")

    def _ensure_unique_plan_key(self, *, tenant_id: str, plan_key: str, exclude_plan_id: str | None = None) -> None:
        stmt = select(MembershipPlan.id).where(
            MembershipPlan.tenant_id == tenant_id,
            MembershipPlan.plan_key == plan_key.strip(),
        )
        if exclude_plan_id:
            stmt = stmt.where(MembershipPlan.id != exclude_plan_id)
        existing = self.session.scalar(stmt)
        if existing is not None:
            raise ValueError(f"membership plan key {plan_key} already exists")

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
