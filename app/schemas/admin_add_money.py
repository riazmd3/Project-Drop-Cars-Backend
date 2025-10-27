# schemas/admin_add_money.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class VehicleOwnerInfoResponse(BaseModel):
    vehicle_owner_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    wallet_balance: int
    aadhar_number: str
    address: str
    city: str
    pincode: str
    account_status: str
    
    class Config:
        from_attributes = True


class SearchVehicleOwnerRequest(BaseModel):
    primary_number: str = Field(..., description="Primary phone number of the vehicle owner")


class AdminAddMoneyRequest(BaseModel):
    vehicle_owner_id: UUID = Field(..., description="ID of the vehicle owner")
    transaction_value: int = Field(..., description="Transaction amount in paise (mandatory)")
    notes: Optional[str] = Field(None, description="Transaction notes")
    reference_value: Optional[str] = Field(None, description="Optional reference string for the transaction")


class AdminAddMoneyResponse(BaseModel):
    transaction_id: UUID
    vehicle_owner_id: UUID
    transaction_value: int
    transaction_img: Optional[str]
    reference_value: Optional[str]
    vehicle_owner_ledger_id: Optional[UUID]
    new_wallet_balance: int
    created_at: datetime
    
    class Config:
        from_attributes = True

