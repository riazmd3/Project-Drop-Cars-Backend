# crud/admin_add_money.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.admin_add_money_to_vehicle_owner import AdminAddMoneyToVehicleOwner
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.models.vehicle_owner import VehicleOwnerCredentials
from app.models.wallet_ledger import WalletLedger, WalletEntryTypeEnum
from typing import Optional
from uuid import UUID
import uuid


def get_vehicle_owner_by_primary_number(db: Session, primary_number: str):
    """Get vehicle owner details by primary number"""
    vehicle_owner_details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.primary_number == primary_number
    ).first()
    
    if not vehicle_owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle owner with primary number {primary_number} not found"
        )
    
    # Get account status from vehicle_owner table
    vehicle_owner = db.query(VehicleOwnerCredentials).filter(
        VehicleOwnerCredentials.id == vehicle_owner_details.vehicle_owner_id
    ).first()
    
    account_status = vehicle_owner.account_status.value if vehicle_owner else "Unknown"
    
    return {
        "vehicle_owner_id": vehicle_owner_details.vehicle_owner_id,
        "full_name": vehicle_owner_details.full_name,
        "primary_number": vehicle_owner_details.primary_number,
        "secondary_number": vehicle_owner_details.secondary_number,
        "wallet_balance": vehicle_owner_details.wallet_balance,
        "aadhar_number": vehicle_owner_details.aadhar_number,
        "address": vehicle_owner_details.address,
        "city": vehicle_owner_details.city,
        "pincode": vehicle_owner_details.pincode,
        "account_status": account_status
    }


def create_admin_add_money_transaction(
    db: Session,
    vehicle_owner_id: str,
    transaction_value: int,
    transaction_img: Optional[str] = None,
    notes: Optional[str] = None,
    reference_value: Optional[str] = None
):
    """Create admin add money transaction and update wallet"""
    
    # Validate transaction_value
    if transaction_value <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction value must be greater than 0"
        )
    
    # Convert vehicle_owner_id to UUID
    try:
        vehicle_owner_id_uuid = UUID(vehicle_owner_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vehicle_owner_id format"
        )
    
    # Get vehicle owner details
    vehicle_owner = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id_uuid
    ).first()
    
    if not vehicle_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner not found"
        )
    
    # Update wallet balance
    balance_before = vehicle_owner.wallet_balance
    new_balance = balance_before + transaction_value
    
    vehicle_owner.wallet_balance = new_balance
    db.add(vehicle_owner)
    
    # Create wallet ledger entry
    ledger_entry = WalletLedger(
        vehicle_owner_id=vehicle_owner_id_uuid,
        reference_id=str(uuid.uuid4()),  # Reference to the admin transaction
        reference_type="ADMIN_ADD_MONEY",
        entry_type=WalletEntryTypeEnum.CREDIT,
        amount=transaction_value,
        balance_before=balance_before,
        balance_after=new_balance,
        notes=notes or f"Admin added money: {transaction_value}"
    )
    db.add(ledger_entry)
    db.flush()  # Get the ID without committing
    wallet_ledger_entry_id = ledger_entry.id
    
    # Create admin add money transaction record
    admin_transaction = AdminAddMoneyToVehicleOwner(
        vehicle_owner_id=vehicle_owner_id_uuid,
        transaction_value=transaction_value,
        transaction_img=transaction_img,
        reference_value=reference_value,
        vehicle_owner_ledger_id=wallet_ledger_entry_id
    )
    
    db.add(admin_transaction)
    db.commit()
    db.refresh(admin_transaction)
    
    return {
        "transaction_id": admin_transaction.id,
        "vehicle_owner_id": admin_transaction.vehicle_owner_id,
        "transaction_value": admin_transaction.transaction_value,
        "transaction_img": admin_transaction.transaction_img,
        "reference_value": admin_transaction.reference_value,
        "vehicle_owner_ledger_id": admin_transaction.vehicle_owner_ledger_id,
        "new_wallet_balance": new_balance,
        "created_at": admin_transaction.created_at
    }


def get_vehicle_owner_details_by_id(db: Session, vehicle_owner_id: str):
    """Get vehicle owner details by ID"""
    vehicle_owner_details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()
    
    if not vehicle_owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner not found"
        )
    
    return vehicle_owner_details

