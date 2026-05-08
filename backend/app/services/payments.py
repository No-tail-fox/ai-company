from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import PaymentOrder, utcnow
from app.services.wallet import WalletService


class PaymentService:
    def __init__(self, session: Session):
        self.session = session

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

