from pydantic import BaseModel, Field, validator
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import Form
from enum import Enum

# Regex pattern for Indian mobile numbers
indian_phone_pattern = r'^(?:\+91)?[6-9]\d{9}$'

class AccountStatusEnum(str, Enum):
    ONLINE = "ONLINE"
    DRIVING = "DRIVING"
    BLOCKED = "BLOCKED"

class CarDriverForm(BaseModel):
    vehicle_owner_id: Optional[UUID] = Field(None, description="Vehicle owner ID (auto-set from token)")
    organization_id: Optional[str] = None
    
    full_name: Annotated[str, Field(
        min_length=3,
        max_length=100,
        description="Full name must be between 3 and 100 characters"
    )]
    
    primary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Primary mobile number must be a valid Indian mobile number"
    )]
    
    secondary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Secondary mobile number must be a valid Indian mobile number"
    )]
    
    password: Annotated[str, Field(
        min_length=6,
        description="Password must be at least 6 characters long"
    )]
    
    licence_number: Annotated[str, Field(
        min_length=5,
        max_length=20,
        description="License number (5-20 characters)"
    )]
    
    adress: Annotated[str, Field(
        min_length=10,
        description="Address must be at least 10 characters long"
    )]

    @validator('primary_number', 'secondary_number')
    def validate_phone_numbers(cls, v):
        import re
        if not re.match(indian_phone_pattern, v):
            raise ValueError('Invalid Indian mobile number format. Use +919876543210 or 9876543210')
        return v

    @validator('licence_number')
    def validate_licence_number(cls, v):
        if not v.replace(' ', '').replace('-', '').isalnum():
            raise ValueError('License number should contain only letters, numbers, spaces, and hyphens')
        return v.upper()

    @classmethod
    def as_form(
        cls,
        vehicle_owner_id: Optional[str] = Form(None, description="Vehicle owner ID (auto-set from token)"),
        full_name: str = Form(..., description="Full name (3-100 characters)"),
        primary_number: str = Form(..., description="Primary mobile number"),
        secondary_number: str = Form(..., description="Secondary mobile number"),
        password: str = Form(..., description="Password (min 6 characters)"),
        licence_number: str = Form(..., description="License number"),
        adress: str = Form(..., description="Address (min 10 characters)"),
        organization_id: Optional[str] = Form(None, description="Organization ID (optional)"),
    ):
        return cls(
            vehicle_owner_id=UUID(vehicle_owner_id) if vehicle_owner_id else None,
            full_name=full_name,
            primary_number=primary_number,
            secondary_number=secondary_number,
            password=password,
            licence_number=licence_number,
            adress=adress,
            organization_id=organization_id,
        )

class CarDriverOut(BaseModel):
    id: UUID
    organization_id: Optional[str]
    full_name: str
    primary_number: str
    secondary_number: str
    licence_number: str
    licence_front_img: Optional[str]
    adress: str
    driver_status: AccountStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "organization_id": "org_123",
                "full_name": "John Doe",
                "primary_number": "+919876543210",
                "secondary_number": "+919876543211",
                "licence_number": "DL-0123456789",
                "licence_front_img": "https://example.com/licence_front.jpg",
                "adress": "123 Main Street, Mumbai",
                "driver_status": "BLOCKED",
                "created_at": "2025-08-13T12:00:00Z"
            }
        }


class CarDriverSignupResponse(BaseModel):
    message: str
    driver_id: str
    license_img_url: str
    status: str

class CarDriverSigninRequest(BaseModel):
    primary_number: str = Field(..., description="Primary mobile number")
    password: str = Field(..., description="Password")

class CarDriverSigninResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    driver_id: str
    full_name: str
    primary_number: str
    driver_status: AccountStatusEnum

class DriverStatusUpdateResponse(BaseModel):
    message: str
    driver_id: str
    new_status: AccountStatusEnum
