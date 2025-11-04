# schemas/admin_management.py
from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from app.models.common_enums import DocumentStatusEnum

# ============ VENDOR SCHEMAS ============

class VendorListResponse(BaseModel):
    """Response schema for vendor list item"""
    id: UUID
    vendor_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    gpay_number: str
    wallet_balance: int
    bank_balance: int
    aadhar_number: str
    aadhar_front_img: Optional[str]
    address: str
    city: str
    pincode: str
    created_at: datetime

    class Config:
        from_attributes = True

class VendorListOut(BaseModel):
    """Response schema for vendor list with pagination"""
    vendors: List[VendorListResponse]
    total_count: int

class VendorDocumentInfo(BaseModel):
    """Vendor document information"""
    document_type: str
    status: Optional[str]
    image_url: Optional[str]

class VendorFullDetailsResponse(BaseModel):
    """Response schema for vendor full details"""
    id: UUID
    vendor_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    gpay_number: str
    wallet_balance: int
    bank_balance: int
    aadhar_number: str
    aadhar_front_img: Optional[str]
    aadhar_status: Optional[str]
    address: str
    city: str
    pincode: str
    account_status: str
    documents: Dict[str, VendorDocumentInfo]
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateAccountStatusRequest(BaseModel):
    """Request schema for updating account status"""
    account_status: str

class UpdateDocumentStatusRequest(BaseModel):
    """Request schema for updating document status"""
    document_status: str

class StatusUpdateResponse(BaseModel):
    """Response schema for status update"""
    message: str
    id: UUID
    new_status: str

# ============ VEHICLE OWNER SCHEMAS ============

class VehicleOwnerListResponse(BaseModel):
    """Response schema for vehicle owner list item"""
    id: UUID
    vehicle_owner_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    wallet_balance: int
    aadhar_number: str
    aadhar_front_img: Optional[str]
    address: str
    city: str
    pincode: str
    created_at: datetime

    class Config:
        from_attributes = True

class VehicleOwnerListOut(BaseModel):
    """Response schema for vehicle owner list with pagination"""
    vehicle_owners: List[VehicleOwnerListResponse]
    total_count: int

class VehicleOwnerDocumentInfo(BaseModel):
    """Vehicle owner document information"""
    document_type: str
    status: Optional[str]
    image_url: Optional[str]

class VehicleOwnerFullDetailsResponse(BaseModel):
    """Response schema for vehicle owner full details"""
    id: UUID
    vehicle_owner_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    wallet_balance: int
    aadhar_number: str
    aadhar_front_img: Optional[str]
    aadhar_status: Optional[str]
    address: str
    city: str
    pincode: str
    account_status: str
    documents: Dict[str, VehicleOwnerDocumentInfo]
    created_at: datetime

    class Config:
        from_attributes = True

# ============ CAR SCHEMAS ============

class CarListItem(BaseModel):
    """Car list item schema"""
    id: UUID
    vehicle_owner_id: UUID
    car_name: str
    car_type: str
    car_number: str
    year_of_the_car: Optional[str]
    rc_front_img_url: Optional[str]
    rc_front_status: Optional[str]
    rc_back_img_url: Optional[str]
    rc_back_status: Optional[str]
    insurance_img_url: Optional[str]
    insurance_status: Optional[str]
    fc_img_url: Optional[str]
    fc_status: Optional[str]
    car_img_url: Optional[str]
    car_img_status: Optional[str]
    car_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CarListResponse(BaseModel):
    """Response schema for car list"""
    cars: List[CarListItem]

# ============ DRIVER SCHEMAS ============

class DriverListItem(BaseModel):
    """Driver list item schema"""
    id: UUID
    vehicle_owner_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    licence_number: str
    licence_front_img: Optional[str]
    licence_front_status: Optional[str]
    address: str
    city: str
    pincode: str
    driver_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DriverListResponse(BaseModel):
    """Response schema for driver list"""
    drivers: List[DriverListItem]

# ============ VEHICLE OWNER WITH CARS AND DRIVERS ============

class VehicleOwnerWithAssetsResponse(BaseModel):
    """Response schema for vehicle owner with cars and drivers"""
    vehicle_owner: VehicleOwnerFullDetailsResponse
    cars: List[CarListItem]
    drivers: List[DriverListItem]
