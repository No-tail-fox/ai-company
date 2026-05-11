from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import PaymentOrder, User, new_id, utcnow
from app.services.wallet import WalletService


RECHARGE_PACKAGES = {
    "points_1000": {"points": 1000, "amount_cents": 990, "name": "1000 points"},
    "points_5000": {"points": 5000, "amount_cents": 4900, "name": "5000 points"},
    "points_10000": {"points": 10000, "amount_cents": 8900, "name": "10000 points"},
}


class PaymentPackageError(Exception):
    pass


class PaymentUserNotFoundError(Exception):
    pass


class PaymentService:
    def __init__(self, session: Session):
        self.session = session

    def create_recharge_order(
        self,
        *,
        tenant_id: str,
        user_id: str,
        package_key: str,
    ) -> dict:
        package = RECHARGE_PACKAGES.get(package_key)
        if package is None:
            raise PaymentPackageError(f"unknown recharge package {package_key}")
        user_exists = self.session.scalar(
            select(User.id).where(
                User.tenant_id == tenant_id,
                User.id == user_id,
            )
        )
        if user_exists is None:
            raise PaymentUserNotFoundError(f"user {user_id} was not found")

        provider_order_no = f"RECHARGE-{utcnow().strftime('%Y%m%d%H%M%S')}-{new_id()[:8].upper()}"
        order = PaymentOrder(
            tenant_id=tenant_id,
            user_id=user_id,
            provider="manual",
            provider_order_no=provider_order_no,
            request_key=f"recharge:{provider_order_no}",
            amount_cents=package["amount_cents"],
            points=package["points"],
            status="PENDING",
            raw_payload={
                "package_key": package_key,
                "package_name": package["name"],
                "message": "待接入支付渠道，支付成功回调后自动入账",
            },
        )
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return self.recharge_order_payload(order)

    def handle_success_callback(
        self,
        *,
        tenant_id: str,
        user_id: str,
        provider: str,
        provider_order_no: str,
        amount_cents: int,
        points: int,
        request_key: str,
        raw_payload: dict,
    ) -> PaymentOrder:
        existing = self.session.scalar(
            select(PaymentOrder).where(
                PaymentOrder.tenant_id == tenant_id,
                or_(
                    PaymentOrder.request_key == request_key,
                    (PaymentOrder.provider == provider) & (PaymentOrder.provider_order_no == provider_order_no),
                ),
            )
        )
        if existing:
            return existing

        order = PaymentOrder(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=provider,
            provider_order_no=provider_order_no,
            request_key=request_key,
            amount_cents=amount_cents,
            points=points,
            status="PAID",
            raw_payload=raw_payload,
            paid_at=utcnow(),
        )
        self.session.add(order)
        WalletService(self.session).recharge(
            tenant_id=tenant_id,
            user_id=user_id,
            amount=points,
            reason=f"{provider} recharge {provider_order_no}",
            request_key=f"payment:{provider}:{provider_order_no}",
        )
        self.session.commit()
        return order

    @staticmethod
    def recharge_order_payload(order: PaymentOrder) -> dict:
        raw_payload = order.raw_payload or {}
        return {
            "id": order.id,
            "tenant_id": order.tenant_id,
            "user_id": order.user_id,
            "provider": order.provider,
            "provider_order_no": order.provider_order_no,
            "request_key": order.request_key,
            "package_key": raw_payload.get("package_key", ""),
            "amount_cents": order.amount_cents,
            "points": order.points,
            "status": order.status,
            "message": raw_payload.get("message", "待接入支付渠道"),
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }
