from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Wallet, WalletReservation, WalletTransaction


class WalletError(Exception):
    pass


class WalletNotFoundError(WalletError):
    pass


class ReservationNotFoundError(WalletError):
    pass


class InsufficientBalanceError(WalletError):
    pass


@dataclass(frozen=True)
class ReservationResult:
    id: str
    request_key: str
    amount: int
    status: str


class WalletService:
    def __init__(self, session: Session):
        self.session = session

    def reserve_funds(
        self,
        *,
        tenant_id: str,
        user_id: str,
        amount: int,
        reason: str,
        request_key: str,
        source_type: str = "GENERATION",
        source_ref: str = "",
    ) -> ReservationResult:
        self._assert_positive(amount)
        existing = self._get_reservation(tenant_id, user_id, request_key)
        if existing:
            return ReservationResult(existing.id, existing.request_key, existing.reserved_amount, existing.status)

        wallet = self._wallet_for_update(tenant_id, user_id)
        if wallet.balance < amount:
            raise InsufficientBalanceError("wallet balance is not enough to reserve this request")

        wallet.balance -= amount
        wallet.frozen_balance += amount

        reservation = WalletReservation(
            tenant_id=tenant_id,
            user_id=user_id,
            wallet_id=wallet.id,
            request_key=request_key,
            reserved_amount=amount,
            settled_amount=0,
            status="RESERVED",
            source_type=source_type,
            source_ref=source_ref,
        )
        transaction = WalletTransaction(
            tenant_id=tenant_id,
            user_id=user_id,
            wallet_id=wallet.id,
            request_key=request_key,
            amount=-amount,
            balance_after=wallet.balance,
            type="CONSUME",
            remark=reason,
            related_ref=source_ref,
        )
        self.session.add_all([reservation, transaction])
        self.session.commit()
        return ReservationResult(reservation.id, reservation.request_key, reservation.reserved_amount, reservation.status)

    def finalize_reservation(
        self,
        *,
        tenant_id: str,
        user_id: str,
        request_key: str,
        estimated_amount: int,
        actual_amount: int,
        reason: str,
    ) -> ReservationResult:
        if actual_amount < 0:
            raise ValueError("actual_amount must be >= 0")

        reservation = self._get_reservation(tenant_id, user_id, request_key)
        if reservation is None:
            raise ReservationNotFoundError(f"reservation {request_key} does not exist")
        if reservation.status == "SETTLED":
            return ReservationResult(reservation.id, reservation.request_key, reservation.reserved_amount, reservation.status)

        wallet = self._wallet_for_update(tenant_id, user_id)
        reserved = reservation.reserved_amount
        if estimated_amount != reserved:
            raise ValueError("estimated_amount must match the original reservation")

        wallet.frozen_balance = max(wallet.frozen_balance - reserved, 0)
        if actual_amount < reserved:
            refund = reserved - actual_amount
            wallet.balance += refund
            self.session.add(
                WalletTransaction(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    wallet_id=wallet.id,
                    request_key=f"{request_key}:refund",
                    amount=refund,
                    balance_after=wallet.balance,
                    type="REFUND",
                    remark=reason,
                    related_ref=reservation.source_ref,
                )
            )
        elif actual_amount > reserved:
            extra_cost = actual_amount - reserved
            if wallet.balance < extra_cost:
                raise InsufficientBalanceError("wallet balance is not enough to settle extra usage")
            wallet.balance -= extra_cost
            self.session.add(
                WalletTransaction(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    wallet_id=wallet.id,
                    request_key=f"{request_key}:extra",
                    amount=-extra_cost,
                    balance_after=wallet.balance,
                    type="CONSUME",
                    remark=reason,
                    related_ref=reservation.source_ref,
                )
            )

        reservation.status = "SETTLED"
        reservation.settled_amount = actual_amount
        self.session.commit()
        return ReservationResult(reservation.id, reservation.request_key, reservation.reserved_amount, reservation.status)

    def recharge(
        self,
        *,
        tenant_id: str,
        user_id: str,
        amount: int,
        reason: str,
        request_key: str,
    ) -> WalletTransaction:
        self._assert_positive(amount)
        existing = self.session.scalar(
            select(WalletTransaction).where(
                WalletTransaction.tenant_id == tenant_id,
                WalletTransaction.request_key == request_key,
            )
        )
        if existing:
            return existing

        wallet = self._wallet_for_update(tenant_id, user_id)
        wallet.balance += amount
        transaction = WalletTransaction(
            tenant_id=tenant_id,
            user_id=user_id,
            wallet_id=wallet.id,
            request_key=request_key,
            amount=amount,
            balance_after=wallet.balance,
            type="RECHARGE",
            remark=reason,
        )
        self.session.add(transaction)
        self.session.commit()
        return transaction

    def _wallet_for_update(self, tenant_id: str, user_id: str) -> Wallet:
        wallet = self.session.scalar(
            select(Wallet)
            .where(Wallet.tenant_id == tenant_id, Wallet.user_id == user_id)
            .with_for_update()
        )
        if wallet is None:
            raise WalletNotFoundError(f"wallet for user {user_id} in tenant {tenant_id} was not found")
        return wallet

    def _get_reservation(self, tenant_id: str, user_id: str, request_key: str) -> WalletReservation | None:
        return self.session.scalar(
            select(WalletReservation).where(
                WalletReservation.tenant_id == tenant_id,
                WalletReservation.user_id == user_id,
                WalletReservation.request_key == request_key,
            )
        )

    @staticmethod
    def _assert_positive(amount: int) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")

