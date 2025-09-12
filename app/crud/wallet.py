from sqlalchemy.orm import Session
from sqlalchemy import select, update
from typing import Optional, Tuple

from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.models.wallet_ledger import WalletLedger, WalletEntryTypeEnum
from app.models.razorpay_transactions import RazorpayTransaction, RazorpayPaymentStatusEnum


def get_owner_balance(db: Session, vehicle_owner_id: str) -> int:
    owner = db.execute(
        select(VehicleOwnerDetails).where(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id)
    ).scalar_one()
    return owner.wallet_balance


def upsert_owner_balance(db: Session, vehicle_owner_id: str, new_balance: int) -> None:
    owner = db.execute(
        select(VehicleOwnerDetails).where(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id)
    ).scalar_one()
    owner.wallet_balance = new_balance
    db.add(owner)


def append_ledger_entry(db: Session, vehicle_owner_id: str, entry_type: WalletEntryTypeEnum,
                        amount: int, balance_before: int, balance_after: int,
                        reference_id: Optional[str] = None, reference_type: Optional[str] = None,
                        notes: Optional[str] = None) -> WalletLedger:
    entry = WalletLedger(
        vehicle_owner_id=vehicle_owner_id,
        entry_type=entry_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_id=reference_id,
        reference_type=reference_type,
        notes=notes,
    )
    db.add(entry)
    return entry


def credit_wallet(db: Session, vehicle_owner_id: str, amount: int, reference_id: Optional[str], reference_type: str, notes: Optional[str] = None) -> Tuple[int, WalletLedger]:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    current = get_owner_balance(db, vehicle_owner_id)
    new_balance = current + amount
    upsert_owner_balance(db, vehicle_owner_id, new_balance)
    entry = append_ledger_entry(
        db, vehicle_owner_id, WalletEntryTypeEnum.CREDIT, amount, current, new_balance, reference_id, reference_type, notes
    )
    return new_balance, entry


def debit_wallet(db: Session, vehicle_owner_id: str, amount: int, reference_id: Optional[str], reference_type: str, notes: Optional[str] = None) -> Tuple[int, WalletLedger]:
    if amount <= 0:
        raise ValueError("Amount must be positive")
    current = get_owner_balance(db, vehicle_owner_id)
    if current < amount:
        raise ValueError("Insufficient balance")
    new_balance = current - amount
    upsert_owner_balance(db, vehicle_owner_id, new_balance)
    entry = append_ledger_entry(
        db, vehicle_owner_id, WalletEntryTypeEnum.DEBIT, amount, current, new_balance, reference_id, reference_type, notes
    )
    return new_balance, entry


def create_rp_transaction(db: Session, vehicle_owner_id: str, rp_order_id: str, amount: int, notes: Optional[str] = None) -> RazorpayTransaction:
    txn = RazorpayTransaction(
        vehicle_owner_id=vehicle_owner_id,
        rp_order_id=rp_order_id,
        amount=amount,
        status=RazorpayPaymentStatusEnum.CREATED,
        notes=notes,
    )
    db.add(txn)
    return txn


def mark_rp_payment_captured(db: Session, rp_order_id: str, rp_payment_id: str, rp_signature: str) -> RazorpayTransaction:
    txn = db.query(RazorpayTransaction).filter(RazorpayTransaction.rp_order_id == rp_order_id).first()
    if not txn:
        raise ValueError("Transaction not found")
    txn.rp_payment_id = rp_payment_id
    txn.rp_signature = rp_signature
    txn.status = RazorpayPaymentStatusEnum.CAPTURED
    txn.captured = True
    db.add(txn)
    return txn


