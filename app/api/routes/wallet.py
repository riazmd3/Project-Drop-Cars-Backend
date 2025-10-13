from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_vehicleOwner_id, get_current_vendor
from app.schemas.wallet import (
    CreateRazorpayOrderRequest,
    CreateRazorpayOrderResponse,
    VerifyRazorpayPaymentRequest,
    RazorpayTransactionOut,
    WalletLedgerOut,
    WalletBalanceOut,
    WalletHistory,
)
from app.utils.razorpay_client import RazorpayClient
from app.crud.wallet import (
    get_owner_balance,
    credit_wallet,
    create_rp_transaction,
    mark_rp_payment_captured,
    check_rp_payment_already_processed,
)
from app.models.wallet_ledger import WalletLedger
from app.models.transfer_transactions import TransferTransactions, TransferStatusEnum
from app.models.vendor_wallet_ledger import VendorWalletLedger
from app.models.razorpay_transactions import RazorpayTransaction, RazorpayPaymentStatusEnum


router = APIRouter()


@router.post("/wallet/razorpay/order", response_model=CreateRazorpayOrderResponse)
def create_rp_order(
    payload: CreateRazorpayOrderRequest,
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    print("check")
    client = RazorpayClient()
    try:
        order = client.create_order(amount_paise=payload.amount, currency=payload.currency, notes=payload.notes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    create_rp_transaction(db, vehicle_owner_id, order.get("id"), order.get("amount"))
    db.commit()

    return CreateRazorpayOrderResponse(rp_order_id=order.get("id"), amount=order.get("amount"), currency=order.get("currency", "INR"))


@router.post("/wallet/razorpay/verify", response_model=RazorpayTransactionOut)
def verify_rp_payment(
    payload: VerifyRazorpayPaymentRequest,
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    # Verify signature
    if not RazorpayClient.verify_signature(payload.rp_order_id, payload.rp_payment_id, payload.rp_signature):
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")

    # Check if payment already processed (idempotency)
    if check_rp_payment_already_processed(db, payload.rp_payment_id):
        # Return existing transaction without processing again
        txn = db.query(RazorpayTransaction).filter(
            RazorpayTransaction.rp_payment_id == payload.rp_payment_id
        ).first()
        if txn:
            return txn
        else:
            raise HTTPException(status_code=400, detail="Payment already processed but transaction not found")

    # Mark captured and credit wallet atomically
    try:
        txn = mark_rp_payment_captured(db, payload.rp_order_id, payload.rp_payment_id, payload.rp_signature)
        
        # Only credit wallet if not already processed
        if txn.status == RazorpayPaymentStatusEnum.CAPTURED and not check_rp_payment_already_processed(db, payload.rp_payment_id):
            new_balance, _ = credit_wallet(
                db,
                vehicle_owner_id=vehicle_owner_id,
                amount=txn.amount,
                reference_id=txn.rp_payment_id,
                reference_type="RAZORPAY_PAYMENT",
                notes="Wallet top-up via Razorpay",
            )
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return txn


@router.get("/wallet/ledger", response_model=List[WalletLedgerOut])
def get_ledger(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    entries = db.query(WalletLedger).filter(WalletLedger.vehicle_owner_id == vehicle_owner_id).order_by(WalletLedger.created_at.desc()).all()
    return entries


@router.get("/wallet/balance", response_model=WalletBalanceOut)
def get_balance_endpoint(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    balance = get_owner_balance(db, vehicle_owner_id)
    return {"vehicle_owner_id": vehicle_owner_id, "current_balance": balance}


@router.get("/vendor/wallet/history", response_model=List[WalletHistory])
def get_ledger(
    db: Session = Depends(get_db),
    vendor_id: str = Depends(get_current_vendor),
):
    # print(vendor_id.id)
    credit = db.query(VendorWalletLedger).filter(VendorWalletLedger.vendor_id == vendor_id.id).order_by(VendorWalletLedger.created_at.desc()).all()
    debit = db.query(TransferTransactions).filter(TransferTransactions.vendor_id == vendor_id.id,
                                                  TransferTransactions.status == TransferStatusEnum.APPROVED).order_by(TransferTransactions.updated_at.desc()).all()
    result = []
    
    for entry in debit:
        result.append(WalletHistory(id=entry.id,
                                    vendor_id=entry.vendor_id,
                                    order_id=None,
                                    # entry_type="DEBIT" if entry.status == "Approved" else "None",
                                    entry_type="DEBIT",
                                    amount=entry.requested_amount,
                                    balance_before=entry.wallet_balance_before,
                                    balance_after=entry.wallet_balance_after,
                                    notes=entry.admin_notes,
                                    created_at=entry.updated_at))
    
    for entry in credit:
        result.append(WalletHistory(id=entry.id,
                                    vendor_id=entry.vendor_id,
                                    order_id=entry.order_id,
                                    entry_type=entry.entry_type,
                                    amount=entry.amount,
                                    balance_before=entry.balance_before,
                                    balance_after=entry.balance_after,
                                    notes=entry.notes,
                                    created_at=entry.created_at))
    result.sort(key=lambda x: x.created_at, reverse=True)
    return result