from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.vendor_details import VendorDetails
from app.models.vendor_wallet_ledger import VendorWalletLedger, VendorLedgerEntryType


def get_vendor_wallet_balance(db: Session, vendor_id: str) -> int:
    vendor_details = db.execute(
        select(VendorDetails).where(VendorDetails.vendor_id == vendor_id)
    ).scalar_one()
    return vendor_details.wallet_balance


def set_vendor_wallet_balance(db: Session, vendor_id: str, new_balance: int) -> None:
    vendor_details = db.execute(
        select(VendorDetails).where(VendorDetails.vendor_id == vendor_id)
    ).scalar_one()
    vendor_details.wallet_balance = new_balance
    db.add(vendor_details)


def append_vendor_ledger_entry(
    db: Session,
    *,
    vendor_id: str,
    order_id: Optional[int],
    entry_type: VendorLedgerEntryType,
    amount: int,
    balance_before: int,
    balance_after: int,
    notes: Optional[str] = None,
) -> VendorWalletLedger:
    entry = VendorWalletLedger(
        vendor_id=vendor_id,
        order_id=order_id,
        entry_type=entry_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        notes=notes,
    )
    db.add(entry)
    return entry


def credit_vendor_wallet(
    db: Session,
    *,
    vendor_id: str,
    amount: int,
    order_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Tuple[int, VendorWalletLedger]:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    before = get_vendor_wallet_balance(db, vendor_id)
    after = before + amount
    set_vendor_wallet_balance(db, vendor_id, after)
    entry = append_vendor_ledger_entry(
        db,
        vendor_id=vendor_id,
        order_id=order_id,
        entry_type=VendorLedgerEntryType.CREDIT,
        amount=amount,
        balance_before=before,
        balance_after=after,
        notes=notes,
    )
    return after, entry


