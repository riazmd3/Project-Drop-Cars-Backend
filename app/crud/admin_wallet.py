from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.admin import Admin
from app.models.admin_wallet_ledger import AdminWalletLedger, AdminLedgerEntryType


def get_admin_balance(db: Session, admin_id: str) -> int:
    """Get admin's current balance"""
    admin = db.execute(
        select(Admin).where(Admin.id == admin_id)
    ).scalar_one()
    return admin.balance


def set_admin_balance(db: Session, admin_id: str, new_balance: int) -> None:
    """Set admin's balance"""
    admin = db.execute(
        select(Admin).where(Admin.id == admin_id)
    ).scalar_one()
    admin.balance = new_balance
    db.add(admin)


def append_admin_ledger_entry(
    db: Session,
    *,
    admin_id: str,
    order_id: Optional[int],
    entry_type: AdminLedgerEntryType,
    amount: int,
    balance_before: int,
    balance_after: int,
    notes: Optional[str] = None,
) -> AdminWalletLedger:
    """Create a ledger entry for admin"""
    entry = AdminWalletLedger(
        admin_id=admin_id,
        order_id=order_id,
        entry_type=entry_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        notes=notes,
    )
    db.add(entry)
    return entry


def credit_admin_wallet(
    db: Session,
    *,
    admin_id: str,
    amount: int,
    order_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Tuple[int, AdminWalletLedger]:
    """Credit amount to admin wallet"""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    before = get_admin_balance(db, admin_id)
    after = before + amount
    set_admin_balance(db, admin_id, after)
    
    entry = append_admin_ledger_entry(
        db,
        admin_id=admin_id,
        order_id=order_id,
        entry_type=AdminLedgerEntryType.CREDIT,
        amount=amount,
        balance_before=before,
        balance_after=after,
        notes=notes,
    )
    return after, entry


def debit_admin_wallet(
    db: Session,
    *,
    admin_id: str,
    amount: int,
    order_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Tuple[int, AdminWalletLedger]:
    """Debit amount from admin wallet"""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    before = get_admin_balance(db, admin_id)
    after = before - amount
    
    if after < 0:
        raise ValueError("Insufficient admin balance")
    
    set_admin_balance(db, admin_id, after)
    
    entry = append_admin_ledger_entry(
        db,
        admin_id=admin_id,
        order_id=order_id,
        entry_type=AdminLedgerEntryType.DEBIT,
        amount=amount,
        balance_before=before,
        balance_after=after,
        notes=notes,
    )
    return after, entry

