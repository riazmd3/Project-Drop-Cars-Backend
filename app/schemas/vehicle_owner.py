from pydantic import BaseModel, Field
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime

# --- Regex pattern for Indian mobile numbers ---
indian_phone_pattern = r'^(?:\+91)?[6-9]\d{9}$'

# --- Base Schema ---
class VehicleOwnerBase(BaseModel):
    organization_id: Optional[str] = None

    full_name: Annotated[str, Field(min_length=3, max_length=100)]

    primary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Indian mobile number, with optional +91 country code"
    )]

    secondary_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Indian mobile number, with optional +91 country code"
    )]

    gpay_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Indian mobile number, with optional +91 country code"
    )]

    password: str
    address: str
    aadhar_number: str
    aadhar_front_img: str

    owner_profile_status: bool = False
    driver_profile: bool = False
    car_profile: bool = False


# --- Output Schema ---
class VehicleOwnerOut(VehicleOwnerBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "organization_id": "org_123",
                "full_name": "Jane Doe",
                "primary_number": "+919876543210",
                "secondary_number": "+919876543211",
                "gpay_number": "+919876543212",
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
