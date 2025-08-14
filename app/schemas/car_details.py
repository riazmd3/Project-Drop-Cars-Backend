from pydantic import BaseModel, Field, validator
from typing import Optional, Annotated
from uuid import UUID
from datetime import datetime
from fastapi import Form
from enum import Enum

class CarTypeEnum(str, Enum):
    SEDAN = "SEDAN"
    SUV = "SUV"
    INNOVA = "INNOVA"

class CarDetailsForm(BaseModel):
    vehicle_owner_id: UUID = Field(..., description="Vehicle owner ID")
    organization_id: Optional[str] = None
    
    car_name: Annotated[str, Field(
        min_length=2,
        max_length=100,
        description="Car name must be between 2 and 100 characters"
    )]
    
    car_type: CarTypeEnum = Field(
        description="Car type: SEDAN, SUV, or INNOVA"
    )
    
    car_number: Annotated[str, Field(
        min_length=5,
        max_length=20,
        description="Car registration number (5-20 characters)"
    )]

    @validator('car_number')
    def validate_car_number(cls, v):
        # Basic validation for car number format
        if not v.replace(' ', '').replace('-', '').isalnum():
            raise ValueError('Car number should contain only letters, numbers, spaces, and hyphens')
        return v.upper()

    @classmethod
    def as_form(
        cls,
        vehicle_owner_id: str = Form(..., description="Vehicle owner ID"),
        car_name: str = Form(..., description="Car name (2-100 characters)"),
        car_type: CarTypeEnum = Form(..., description="Car type: SEDAN, SUV, or INNOVA"),
        car_number: str = Form(..., description="Car registration number"),
        organization_id: Optional[str] = Form(None, description="Organization ID (optional)"),
    ):
        return cls(
            vehicle_owner_id=UUID(vehicle_owner_id),
            car_name=car_name,
            car_type=car_type,
            car_number=car_number,
            organization_id=organization_id,
        )

class CarDetailsOut(BaseModel):
    id: UUID
    organization_id: Optional[str]
    car_name: str
    car_type: CarTypeEnum
    car_number: str
    rc_front_img_url: Optional[str]
    rc_back_img_url: Optional[str]
    insurance_img_url: Optional[str]
    fc_img_url: Optional[str]
    car_img_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "organization_id": "org_123",
                "car_name": "Toyota Camry",
                "car_type": "SEDAN",
                "car_number": "MH-12-AB-1234",
                "rc_front_img_url": "https://example.com/rc_front.jpg",
                "rc_back_img_url": "https://example.com/rc_back.jpg",
                "insurance_img_url": "https://example.com/insurance.jpg",
                "fc_img_url": "https://example.com/fc.jpg",
                "car_img_url": "https://example.com/car.jpg",
                "created_at": "2025-08-13T12:00:00Z"
            }
        }


class CarDetailsSignupResponse(BaseModel):
    message: str
    car_id: str
    image_urls: dict
    status: str
