import pytest

from app.models import Tenant, User, Wallet
from app.services.wallet import InsufficientBalanceError, WalletService


def test_wallet_reserve_and_refund_keeps_balances_consistent(session):
    tenant = Tenant(id="tenant-acme", slug="acme", name="Acme")
    user = User(id="user-acme", tenant_id=tenant.id, phone="13800000000", role="USER")
    wallet = Wallet(id="wallet-acme", tenant_id=tenant.id, user_id=user.id, balance=1000, frozen_balance=0)
    session.add_all([tenant, user, wallet])
    session.commit()

    service = WalletService(session)

    reservation = service.reserve_funds(
        tenant_id=tenant.id,
        user_id=user.id,
        amount=200,
        reason="video generation",
        request_key="task-888",
    )

    assert reservation.amount == 200
    assert wallet.balance == 800
    assert wallet.frozen_balance == 200

    service.finalize_reservation(
        tenant_id=tenant.id,
        user_id=user.id,
        request_key="task-888",
        estimated_amount=200,
        actual_amount=50,
        reason="video generation settled",
    )

    assert wallet.balance == 950
    assert wallet.frozen_balance == 0


def test_wallet_rejects_overdraft(session):
    tenant = Tenant(id="tenant-acme", slug="acme", name="Acme")
    user = User(id="user-acme", tenant_id=tenant.id, phone="13800000000", role="USER")
    wallet = Wallet(id="wallet-acme", tenant_id=tenant.id, user_id=user.id, balance=100, frozen_balance=0)
    session.add_all([tenant, user, wallet])
    session.commit()

    service = WalletService(session)

    with pytest.raises(InsufficientBalanceError):
        service.reserve_funds(
            tenant_id=tenant.id,
            user_id=user.id,
            amount=200,
            reason="too expensive",
            request_key="task-overdraft",
        )
