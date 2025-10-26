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
    deduct_admin_profit: bool = False,
    admin_profit: Optional[int] = None,
    admin_id: Optional[str] = None,
) -> Tuple[int, VendorWalletLedger]:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    before = get_vendor_wallet_balance(db, vendor_id)
    
    # If admin profit needs to be deducted
    if deduct_admin_profit and admin_profit and admin_profit > 0:
        # First credit the full amount to vendor
        after = before + amount
        set_vendor_wallet_balance(db, vendor_id, after)
        
        # Then debit admin_profit from vendor
        final_after = after - admin_profit
        set_vendor_wallet_balance(db, vendor_id, final_after)
        
        # Create ledger entry for credit of full amount
        credit_entry = append_vendor_ledger_entry(
            db,
            vendor_id=vendor_id,
            order_id=order_id,
            entry_type=VendorLedgerEntryType.CREDIT,
            amount=amount,
            balance_before=before,
            balance_after=after,
            notes=notes or f"Trip {order_id} vendor profit",
        )
        
        # Create ledger entry for admin profit debit
        debit_entry = append_vendor_ledger_entry(
            db,
            vendor_id=vendor_id,
            order_id=order_id,
            entry_type=VendorLedgerEntryType.DEBIT,
            amount=admin_profit,
            balance_before=after,
            balance_after=final_after,
            notes=f"Admin profit deduction for order {order_id}",
        )
        
        # Credit admin wallet with admin profit
        if admin_id:
            from app.crud.admin_wallet import credit_admin_wallet
            credit_admin_wallet(
                db,
                admin_id=admin_id,
                amount=admin_profit,
                order_id=order_id,
                notes=f"Admin profit from order {order_id}"
            )
        
        return final_after, credit_entry
    else:
        # Normal credit without admin profit deduction
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


def debit_vendor_wallet(
    db: Session,
    *,
    vendor_id: str,
    amount: int,
    order_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Tuple[int, VendorWalletLedger]:
    """Debit amount from vendor wallet"""
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    before = get_vendor_wallet_balance(db, vendor_id)
    after = before - amount
    
    if after < 0:
        raise ValueError("Insufficient vendor balance")
    
    set_vendor_wallet_balance(db, vendor_id, after)
    
    entry = append_vendor_ledger_entry(
        db,
        vendor_id=vendor_id,
        order_id=order_id,
        entry_type=VendorLedgerEntryType.DEBIT,
        amount=amount,
        balance_before=before,
        balance_after=after,
        notes=notes,
    )
    return after, entry


