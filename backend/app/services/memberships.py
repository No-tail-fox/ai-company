from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MembershipPlan, UserMembership, utcnow


class MembershipService:
    def __init__(self, session: Session):
        self.session = session

    def can_use_entitlement(self, *, tenant_id: str, user_id: str, entitlement: str) -> bool:
        now = utcnow()
        memberships = self.session.execute(
            select(UserMembership, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.id == UserMembership.plan_id)
            .where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE",
                UserMembership.expires_at > now,
                MembershipPlan.enabled.is_(True),
            )
        ).all()
        for _, plan in memberships:
            if entitlement in (plan.entitlements or []):
                return True
        return False

    def get_status(self, *, tenant_id: str, user_id: str) -> dict:
        now = utcnow()
        row = self.session.execute(
            select(UserMembership, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.id == UserMembership.plan_id)
            .where(
                UserMembership.tenant_id == tenant_id,
                UserMembership.user_id == user_id,
                UserMembership.status == "ACTIVE",
                UserMembership.expires_at > now,
            )
            .order_by(UserMembership.expires_at.desc())
        ).first()
        if row is None:
            return {"active": False, "plan": None, "entitlements": []}
        membership, plan = row
        return {
            "active": True,
            "plan": {"id": plan.id, "plan_key": plan.plan_key, "name": plan.name},
            "expires_at": membership.expires_at.isoformat(),
            "entitlements": plan.entitlements or [],
        }

