from pydantic import BaseModel, Field, validator
from typing import Optional, List, Annotated
from uuid import UUID
from datetime import datetime
from app.models.order_assignments import AssignmentStatusEnum

# Regex pattern for Indian mobile numbers (10 digits only, starting with 6-9)
indian_phone_pattern = r'^[6-9]\d{9}$'

class OrderAssignmentCreate(BaseModel):
    order_id: int

class OrderAssignmentResponse(BaseModel):
    id: int
    order_id: int
    vehicle_owner_id: UUID
    driver_id: Optional[UUID] = None
    car_id: Optional[UUID] = None
    assignment_status: AssignmentStatusEnum
    assigned_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OrderAssignmentStatusUpdate(BaseModel):
    assignment_status: AssignmentStatusEnum

class OrderAssignmentWithOrderDetails(BaseModel):
    # Order assignment details
    # id: Optional[int] = None
    order_id: int
    vehicle_owner_id: UUID
    # driver_id: Optional[UUID] = None
    # car_id: Optional[UUID] = None
    assignment_status: AssignmentStatusEnum
    # assigned_at: Optional[datetime] = None
    # expires_at: Optional[datetime] = None
    # cancelled_at: Optional[datetime] = None
    # completed_at: Optional[datetime] = None
    created_at: datetime
    
    # Order details
    vendor_id: UUID
    trip_type: str
    car_type: str
    pickup_drop_location: dict
    start_date_time: datetime
    customer_name: str
    customer_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Customer mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]
    # cost_per_km: int
    # extra_cost_per_km: int
    # driver_allowance: int
    # extra_driver_allowance: int
    # permit_charges: int
    # extra_permit_charges: int
    # hill_charges: int
    # toll_charges: int
    pickup_notes: Optional[str] = None
    trip_status: str
    pick_near_city: str
    trip_distance: int
    trip_time: str
    platform_fees_percent: int
    estimated_price: Optional[int] = None
    vendor_price: Optional[int] = None
    order_created_at: datetime

    class Config:
        from_attributes = True
        
class vehicle_owner_pending(BaseModel):
    # Order assignment details
    # id: Optional[int] = None
    order_id: int
    vehicle_owner_id: UUID
    # driver_id: Optional[UUID] = None
    # car_id: Optional[UUID] = None
    assignment_status: AssignmentStatusEnum
    # assigned_at: Optional[datetime] = None
    # expires_at: Optional[datetime] = None
    # cancelled_at: Optional[datetime] = None
    # completed_at: Optional[datetime] = None
    created_at: datetime
    
    # Order details
    vendor_id: UUID
    trip_type: str
    car_type: str
    pickup_drop_location: dict
    start_date_time: datetime
    customer_name: str
    customer_number: Annotated[str, Field(
        pattern=indian_phone_pattern,
        description="Customer mobile number must be a valid 10-digit Indian mobile number (starting with 6-9)"
    )]
    # cost_per_km: int
    # extra_cost_per_km: int
    # driver_allowance: int
    # extra_driver_allowance: int
    # permit_charges: int
    # extra_permit_charges: int
    # hill_charges: int
    # toll_charges: int
    pickup_notes: Optional[str] = None
    trip_status: str
    pick_near_city: str
    trip_distance: int
    trip_time: str
    platform_fees_percent: int
    max_time_to_assign_order : Optional[datetime]
    estimated_price: Optional[int] = None
    vendor_price: Optional[int] = None
    order_created_at: datetime

    class Config:
        from_attributes = True

class UpdateCarDriverRequest(BaseModel):
    driver_id: UUID
    car_id: UUID

class StartTripRequest(BaseModel):
    start_km: int = Field(..., gt=0, description="Starting kilometer reading")
    
    @validator('start_km')
    def validate_start_km(cls, v):
        if v <= 0:
            raise ValueError('Start KM must be greater than 0')
        return v

class StartTripResponse(BaseModel):
    message: str
    end_record_id: int
    start_km: int
    speedometer_img_url: str

class EndTripRequest(BaseModel):
    end_km: int = Field(..., gt=0, description="Ending kilometer reading")
    
    @validator('end_km')
    def validate_end_km(cls, v):
        if v <= 0:
            raise ValueError('End KM must be greater than 0')
        return v

class EndTripResponse(BaseModel):
    message: str
    end_record_id: int
    end_km: int
    close_speedometer_img_url: Optional[str] = None
    total_km: int
    # calculated_fare: int
    # driver_amount: int
    # vehicle_owner_amount: int

class DriverOrderListResponse(BaseModel):
    id: int
    order_id: int
    assignment_status: AssignmentStatusEnum
    customer_name: str
    customer_number: str
    pickup_drop_location: dict
    start_date_time: datetime
    trip_type: str
    car_type: str
    trip_distance: int
    trip_time: str
    toll_charge_update: Optional[bool] = None
    data_visibility_vehicle_owner: Optional[bool] = None
    closed_vendor_price: Optional[int] = None
    estimated_price: Optional[int] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
        
class DriverOrderReport(BaseModel):
    # # id: int
    # #Assignment details
    # order_id: int
    # trip_status: AssignmentStatusEnum
    
    # #Order details
    # customer_name: str
    # customer_number: str
    # pickup_drop_location: dict
    # start_date_time: datetime
    # trip_type: str
    # car_type: str
    # trip_distance: int
    # trip_time: str
    # # toll_charge_updated_toll_chargeupdate: Optional[bool] = None
    # # data_visibility_vehicle_owner: Optional[bool] = None
    # # closed_vendor_price: Optional[int] = None
    # customer_price: Optional[int] = None
    # assigned_at: Optional[datetime] = None
    # created_at: datetime
    # completed_at: datetime
    # class Config:
    #     from_attributes = True
        # Assignment details
        
    order_id: int  # depending on your DB, adjust as needed
    trip_status: str

    # Order details
    customer_name: str
    customer_number: str
    pickup_drop_location: dict
    start_date_time: datetime
    trip_type: str = "Unknown"
    car_type: str = "Unknown"
    trip_time: Optional[str]  # Could be timedelta or string depending on your model
    trip_distance: Optional[float] = None
    toll_charges: Optional[float]
    customer_price: Optional[float]

    # Hourly Rental details (optional - only if hourly_rental is present)
    package_hours: Optional[dict] = None
    cost_per_hour: Optional[float] = None
    cost_per_km: Optional[float] = None

    # New Order details (optional - only if hourly_rental is not present)
    driver_allowance: Optional[float] = None
    permit_charges: Optional[float] = None
    hill_charges: Optional[float] = None
    pickup_notes: Optional[str] = None

    # Timestamps
    assigned_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_km : int

    # Additional toll field for clarity/debugging if needed
    updated_toll_charge: Optional[float] = None