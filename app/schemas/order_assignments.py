from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime
from app.models.order_assignments import AssignmentStatusEnum


class OrderAssignmentCreate(BaseModel):
    order_id: int


class OrderAssignmentResponse(BaseModel):
    id: int
    order_id: int
    vehicle_owner_id: UUID4
    driver_id: Optional[UUID4] = None
    car_id: Optional[UUID4] = None
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
    id: int
    order_id: int
    vehicle_owner_id: UUID4
    driver_id: Optional[UUID4] = None
    car_id: Optional[UUID4] = None
    assignment_status: AssignmentStatusEnum
    assigned_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    # Order details
    vendor_id: UUID4
    trip_type: str
    car_type: str
    pickup_drop_location: dict
    start_date_time: datetime
    customer_name: str
    customer_number: str
    cost_per_km: int
    extra_cost_per_km: int
    driver_allowance: int
    extra_driver_allowance: int
    permit_charges: int
    extra_permit_charges: int
    hill_charges: int
    toll_charges: int
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
