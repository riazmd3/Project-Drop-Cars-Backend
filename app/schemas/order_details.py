from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.order_assignments import AssignmentStatusEnum


class VendorBasicInfo(BaseModel):
    """Basic vendor information for order details"""
    id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str] = None
    gpay_number: str
    aadhar_number: str
    address: str
    wallet_balance: int
    bank_balance: int
    created_at: datetime

    class Config:
        from_attributes = True


class DriverBasicInfo(BaseModel):
    """Basic driver information for order details"""
    id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str] = None
    licence_number: str
    address: str
    driver_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CarBasicInfo(BaseModel):
    """Basic car information for order details"""
    id: UUID
    car_name: str
    car_type: str
    car_number: str
    car_status: str
    rc_front_img_url: Optional[str] = None
    rc_back_img_url: Optional[str] = None
    insurance_img_url: Optional[str] = None
    fc_img_url: Optional[str] = None
    car_img_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VehicleOwnerBasicInfo(BaseModel):
    """Basic vehicle owner information for order details"""
    id: UUID
    full_name: str
    primary_number: str
    secondary_number: Optional[str] = None
    address: str
    account_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderAssignmentDetail(BaseModel):
    """Order assignment details"""
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


class EndRecordDetail(BaseModel):
    """End record details"""
    id: int
    order_id: int
    driver_id: UUID
    start_km: int
    end_km: int
    contact_number: str
    img_url: str
    close_speedometer_image: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminOrderDetailResponse(BaseModel):
    """Full order details response for admin - includes all related data"""
    # Order basic information
    id: int
    source: str
    source_order_id: int
    vendor_id: UUID
    trip_type: str
    car_type: str
    pickup_drop_location: Dict[str, Any]
    start_date_time: datetime
    customer_name: str
    customer_number: str
    trip_status: Optional[str] = None
    pick_near_city: Optional[str] = None
    trip_distance: Optional[int] = None
    trip_time: Optional[str] = None
    estimated_price: Optional[int] = None
    vendor_price: Optional[int] = None
    platform_fees_percent: Optional[int] = None
    closed_vendor_price: Optional[int] = None
    closed_driver_price: Optional[int] = None
    commision_amount: Optional[int] = None
    created_at: datetime

    # Related data
    vendor: VendorBasicInfo
    assignments: List[OrderAssignmentDetail] = []
    end_records: List[EndRecordDetail] = []
    
    # Driver and car info from latest assignment
    assigned_driver: Optional[DriverBasicInfo] = None
    assigned_car: Optional[CarBasicInfo] = None
    vehicle_owner: Optional[VehicleOwnerBasicInfo] = None

    class Config:
        from_attributes = True


class VendorOrderDetailResponse(BaseModel):
    """Limited order details response for vendor - excludes sensitive user data"""
    # Order basic information
    id: int
    source: str
    source_order_id: int
    vendor_id: UUID
    trip_type: str
    car_type: str
    pickup_drop_location: Dict[str, Any]
    start_date_time: datetime
    customer_name: str
    customer_number: str
    trip_status: Optional[str] = None
    pick_near_city: Optional[str] = None
    trip_distance: Optional[int] = None
    trip_time: Optional[str] = None
    estimated_price: Optional[int] = None
    vendor_price: Optional[int] = None
    platform_fees_percent: Optional[int] = None
    closed_vendor_price: Optional[int] = None
    closed_driver_price: Optional[int] = None
    commision_amount: Optional[int] = None
    created_at: datetime

    # Limited assignment info (no sensitive user data)
    assignments: List[OrderAssignmentDetail] = []
    end_records: List[EndRecordDetail] = []
    
    # Basic driver and car info (no personal details)
    assigned_driver_name: Optional[str] = None
    assigned_driver_phone: Optional[str] = None
    assigned_car_name: Optional[str] = None
    assigned_car_number: Optional[str] = None
    vehicle_owner_name: Optional[str] = None
    # cost_per_km : Optional[int] = None
    vendor_profit : Optional[int] = None
    admin_profit : Optional[int] = None
    
    

    class Config:
        from_attributes = True


class VehicleOwnerOrderDetailResponse(BaseModel):
    """Order details response for vehicle owner - includes order and assignment information"""
    # Order basic information
    id: int
    source: str
    source_order_id: int
    vendor_id: UUID
    trip_type: str
    car_type: str
    pickup_drop_location: Dict[str, Any]
    start_date_time: datetime
    customer_name: str
    customer_number: str
    trip_status: Optional[str] = None
    pick_near_city: Optional[str] = None
    trip_distance: Optional[int] = None
    trip_time: Optional[str] = None
    estimated_price: Optional[int] = None
    vendor_price: Optional[int] = None
    platform_fees_percent: Optional[int] = None
    closed_vendor_price: Optional[int] = None
    closed_driver_price: Optional[int] = None
    commision_amount: Optional[int] = None
    created_at: datetime
    cancelled_by : Optional[str] = None
    max_time_to_assign_order : Optional[datetime] = None

    # Assignment information for this vehicle owner
    assignment_id: int
    assignment_status: AssignmentStatusEnum
    assigned_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assignment_created_at: datetime

    # Basic vendor info (no sensitive data)
    vendor_name: Optional[str] = None
    vendor_phone: Optional[str] = None

    # Driver and car info if assigned
    assigned_driver_name: Optional[str] = None
    assigned_driver_phone: Optional[str] = None
    assigned_car_name: Optional[str] = None
    assigned_car_number: Optional[str] = None

    class Config:
        from_attributes = True