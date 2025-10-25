from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, Body
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database.session import get_db
from app.core.security import get_current_vendor, get_current_driver, get_current_admin, get_current_vehicleOwner_id
from app.schemas.new_orders import UnifiedOrder, CloseOrderResponse, Vendor_Pending_Order_Responce
from app.schemas.order_details import AdminOrderDetailResponse, VendorOrderDetailResponse, VehicleOwnerOrderDetailResponse
from app.crud.orders import get_all_orders, get_vendor_orders, close_order, get_vendor_pending_orders, set_vehicle_owner_visibility, get_max_time_to_assign_by_trip_type
from app.crud.order_details import get_admin_order_details, get_vendor_order_details, get_vehicle_owner_pending_orders, get_vehicle_owner_non_pending_orders


router = APIRouter()


@router.get("/all", response_model=List[UnifiedOrder])
def list_all_orders(db: Session = Depends(get_db)):
    return get_all_orders(db)


@router.get("/vendor", response_model=List[UnifiedOrder])
def list_vendor_orders(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    # print(current_vendor.id)
    print("Function executing")
    return get_vendor_orders(db, current_vendor.id)

@router.get("/pending/vendor", response_model=List[Vendor_Pending_Order_Responce])
def list_vendor_orders(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    print("function check")
    return get_vendor_pending_orders(db, current_vendor.id)


@router.get("/admin/{order_id}", response_model=AdminOrderDetailResponse)
async def get_admin_order_details_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get full order details for admin with all related data including:
    - Order information
    - Vendor details
    - Assignment history
    - End records
    - Driver and car information
    - Vehicle owner information
    """
    order_details = get_admin_order_details(db, order_id)
    if not order_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order_details


@router.get("/vendor/{order_id}", response_model=VendorOrderDetailResponse)
async def get_vendor_order_details_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    """
    Get limited order details for vendor with order-related data but excluding sensitive user information:
    - Order information
    - Assignment history
    - End records
    - Basic driver and car info (names and phone numbers only)
    - No personal details like addresses, IDs, etc.
    """
    print("checksss 3")
    print(current_vendor.id)
    order_details = get_vendor_order_details(db, order_id, str(current_vendor.id))
    if not order_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to view this order"
        )
    
    return order_details


@router.post("/{order_id}/close", response_model=CloseOrderResponse)
async def close_order_endpoint(
    order_id: int,
    closed_vendor_price: int = Form(...),
    closed_driver_price: int = Form(...),
    commision_amount: int = Form(...),
    start_km: int = Form(...),
    end_km: int = Form(...),
    contact_number: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_driver=Depends(get_current_driver),
):
    try:
        order, end_record, img_url = close_order(
            db,
            order_id=order_id,
            closed_vendor_price=closed_vendor_price,
            closed_driver_price=closed_driver_price,
            commision_amount=commision_amount,
            driver_id=current_driver.id,
            start_km=start_km,
            end_km=end_km,
            contact_number=contact_number,
            image_file=image,
        )
        return CloseOrderResponse(order_id=order.id, end_record_id=end_record.id, img_url=img_url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/vehicle-owner/pending", response_model=List[VehicleOwnerOrderDetailResponse])
async def get_vehicle_owner_pending_orders_endpoint(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """
    Get all pending orders for the authenticated vehicle owner.
    
    This endpoint returns orders where the assignment_status is 'PENDING' for the vehicle owner.
    The vehicle owner ID is extracted from the JWT token.
    
    Returns:
    - List of orders with assignment_status = 'PENDING'
    - Order details including customer info, trip details, vendor info
    - Assignment information specific to this vehicle owner
    - Driver and car information if assigned
    """
    try:
        orders = get_vehicle_owner_pending_orders(db, vehicle_owner_id)
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving pending orders: {str(e)}"
        )


@router.get("/vehicle-owner/non-pending", response_model=List[VehicleOwnerOrderDetailResponse])
async def get_vehicle_owner_non_pending_orders_endpoint(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """
    Get all non-pending orders for the authenticated vehicle owner.
    
    This endpoint returns orders where the assignment_status is NOT 'PENDING' for the vehicle owner.
    This includes orders with status: ASSIGNED, CANCELLED, COMPLETED, DRIVING.
    The vehicle owner ID is extracted from the JWT token.
    
    Returns:
    - List of orders with assignment_status != 'PENDING'
    - Order details including customer info, trip details, vendor info
    - Assignment information specific to this vehicle owner
    - Driver and car information if assigned
    """
    try:
        orders = get_vehicle_owner_non_pending_orders(db, vehicle_owner_id)
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving non-pending orders: {str(e)}"
        )


@router.patch("/{order_id}/visibility/vehicle-owner/show")
async def show_customer_to_vehicle_owner(
    order_id: int,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    """Vendor-only: allow vehicle owners to see customer data for this order."""
    try:
        order = set_vehicle_owner_visibility(db, order_id, str(current_vendor.id), True)
        return {"order_id": order.id, "data_visibility_vehicle_owner": True}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{order_id}/visibility/vehicle-owner/hide")
async def hide_customer_from_vehicle_owner(
    order_id: int,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    """Vendor-only: hide customer data from vehicle owners for this order."""
    try:
        order = set_vehicle_owner_visibility(db, order_id, str(current_vendor.id), False)
        return {"order_id": order.id, "data_visibility_vehicle_owner": False}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


class UpdateVisibilityRequest(BaseModel):
    data_visibility_vehicle_owner: bool


@router.patch("/{order_id}/visibility/vehicle-owner")
async def update_data_visibility_vehicle_owner(
    order_id: int,
    request: UpdateVisibilityRequest,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    """
    Vendor-only: Update visibility of customer data for vehicle owners.
    
    Args:
        order_id: The ID of the order
        request: Request body containing data_visibility_vehicle_owner boolean
    
    Returns:
        Updated order ID and visibility status
    """
    try:
        order = set_vehicle_owner_visibility(db, order_id, str(current_vendor.id), request.data_visibility_vehicle_owner)
        return {
            "order_id": order.id, 
            "data_visibility_vehicle_owner": request.data_visibility_vehicle_owner
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/max-assignment-times")
async def get_max_assignment_times(
    db: Session = Depends(get_db),
):
    """
    Get the maximum time to assign orders for each trip type based on historical data.
    Returns the maximum time in minutes for oneway, roundtrip, multicity, and hourly rental.
    """
    try:
        max_times = get_max_time_to_assign_by_trip_type(db)
        return {
            "max_assignment_times": max_times,
            "description": "Maximum time in minutes to assign orders for each trip type based on historical data"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving max assignment times: {str(e)}"
        )

