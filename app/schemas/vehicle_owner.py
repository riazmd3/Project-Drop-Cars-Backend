from pydantic import BaseModel, Field, validator
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import Form

# --- Regex pattern for Indian mobile numbers (10 digits only, starting with 6-9) ---
indian_phone_pattern = r'^[6-9]\d{9}$'

# --- Base Schema ---
class VehicleOwnerBase(BaseModel):
    organization_id: Optional[str] = None

    full_name: Annotated[str, Field(min_length=3, max_length=100)]

    primary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Primary mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]

    secondary_number: Optional[Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Secondary mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]] = None

    password: str
    address: str
    city: str
    pincode: str
    aadhar_number: str
    aadhar_front_img: str

    owner_profile_status: bool = False
    driver_profile: bool = False
    car_profile: bool = False


# --- Form Schema for validation without image ---
class VehicleOwnerForm(BaseModel):
    organization_id: Optional[str] = None

    full_name: Annotated[str, Field(
        min_length=3, 
        max_length=100,
        description="Full name must be between 3 and 100 characters"
    )]

    primary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Primary mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]

    secondary_number: Optional[Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Secondary mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]] = None

    password: Annotated[str, Field(
        min_length=6,
        description="Password must be at least 6 characters long"
    )]
    
    address: Annotated[str, Field(
        min_length=10,
        description="Address must be at least 10 characters long"
    )]
    city: Annotated[str, Field(
        min_length=2,
        max_length=100,
        description="City must be between 2 and 100 characters"
    )]
    pincode: Annotated[str, Field(
        min_length=6,
        max_length=6,
        description="Pincode must be exactly 6 digits"
    )]
    aadhar_number: Annotated[str, Field(
        min_length=12,
        max_length=12,
        description="Aadhar number must be exactly 12 digits"
    )]

    @validator('aadhar_number')
    def validate_aadhar_number(cls, v):
        if not v.isdigit():
            raise ValueError('Aadhar number must contain only digits')
        if len(v) != 12:
            raise ValueError('Aadhar number must be exactly 12 digits')
        return v

    @validator('primary_number', 'secondary_number')
    def validate_phone_numbers(cls, v):
        if v is None:  # Allow None for secondary_number
            return v
        import re
        if not re.match(indian_phone_pattern, v):
            raise ValueError('Invalid Indian mobile number format. Use 10-digit number starting with 6-9 (e.g., 9876543210)')
        return v

    @classmethod
    def as_form(
        cls,
        full_name: str = Form(..., description="Full name (3-100 characters)"),
        primary_number: str = Form(..., description="Primary mobile number"),
        secondary_number: Optional[str] = Form(None, description="Secondary mobile number (optional)"),
        password: str = Form(..., description="Password (min 6 characters)"),
        address: str = Form(..., description="Address (min 10 characters)"),
        city: str = Form(..., description="City"),
        pincode: str = Form(..., description="Pincode (6 digits)"),
        aadhar_number: str = Form(..., description="Aadhar number (12 digits)"),
        organization_id: Optional[str] = Form(None, description="Organization ID (optional)"),
    ):
        return cls(
            full_name=full_name,
            primary_number=primary_number,
            secondary_number=secondary_number,
            password=password,
            address=address,
            city=city,
            pincode=pincode,
            aadhar_number=aadhar_number,
            organization_id=organization_id,
        )


# --- Output Schema ---
class VehicleOwnerOut(VehicleOwnerBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "organization_id": "org_123",
                "full_name": "Jane Doe",
                "primary_number": "9876543210",
                "secondary_number": "9876543211",
                "password": "secret123",
                "address": "123 Main Street, Mumbai",
                "aadhar_number": "123456789012",
                "aadhar_front_img": "https://example.com/aadhar_front.jpg",
                "owner_profile_status": False,
                "driver_profile": False,
                "car_profile": False,
                "created_at": "2025-08-13T12:00:00Z"
            }
        }
# schemas.py

class UserLogin(BaseModel):
    mobile_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]
    password: str
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        import re
        if not re.match(indian_phone_pattern, v):
            raise ValueError('Invalid Indian mobile number format. Use 10-digit number starting with 6-9 (e.g., 9876543210)')
        return v
    
class VehicleOwnerDetailsResponse(BaseModel):
    id: UUID
    vehicle_owner_id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str]
    wallet_balance: int
    aadhar_number: str
    city:Optional[str]
    pincode: Optional[str]
    aadhar_front_img: Optional[str]
    address: str
    created_at: datetime

    class Config:
        orm_mode = True