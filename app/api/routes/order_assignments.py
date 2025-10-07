from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_user, get_current_vehicleOwner_id, get_current_driver
from app.schemas.order_assignments import (
    OrderAssignmentCreate,
    OrderAssignmentResponse,
    OrderAssignmentStatusUpdate,
    OrderAssignmentWithOrderDetails,
    UpdateCarDriverRequest,
    StartTripRequest,
    StartTripResponse,
    EndTripRequest,
    EndTripResponse,
    DriverOrderListResponse
)
from app.crud.order_assignments import (
    create_order_assignment,
    get_order_assignment_by_id,
    get_order_assignments_by_vehicle_owner_id,
    get_order_assignments_by_order_id,
    update_assignment_status,
    cancel_assignment,
    complete_assignment,
    get_vendor_orders_with_assignments,
    update_assignment_car_driver,
    get_driver_assigned_orders,
    check_vehicle_owner_balance
)
from app.models.order_assignments import AssignmentStatusEnum

router = APIRouter()


@router.get("/available-drivers")
async def get_available_drivers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all available drivers with ONLINE status for the authenticated vehicle owner"""
    # Get vehicle_owner_id from the authenticated user
    vehicle_owner_id = str(current_user.vehicle_owner_id)
    
    from app.crud.car_driver import get_available_drivers
    available_drivers = get_available_drivers(db, vehicle_owner_id)
    return available_drivers


@router.get("/available-cars")
async def get_available_cars(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all available cars with ONLINE status for the authenticated vehicle owner"""
    # Get vehicle_owner_id from the authenticated user
    vehicle_owner_id = str(current_user.vehicle_owner_id)
    
    from app.crud.car_details import get_available_cars
    available_cars = get_available_cars(db, vehicle_owner_id)
    return available_cars


@router.get("/vehicle_owner/pending", response_model=List[OrderAssignmentWithOrderDetails])
async def get_pending_orders_for_vehicle_owner(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get pending orders for the authenticated vehicle owner based on business rules"""
    try:
        # Get vehicle_owner_id from the authenticated user
        vehicle_owner_id = str(current_user.vehicle_owner_id)
        
        from app.crud.order_assignments import get_pending_orders_for_vehicle_owner
        pending_orders = get_pending_orders_for_vehicle_owner(db, vehicle_owner_id)
        
        # Log the number of orders found for debugging
        print(f"Found {len(pending_orders)} pending orders for vehicle owner {vehicle_owner_id}")
        
        return pending_orders
    except Exception as e:
        print(f"Error in get_pending_orders_for_vehicle_owner: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/acceptorder", response_model=OrderAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def accept_order(
    payload: OrderAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Accept an order and create assignment with balance check"""
    try:
        # Get vehicle_owner_id from the authenticated user
        vehicle_owner_id = str(current_user.vehicle_owner_id)

        # Get order details to check estimated price
        from app.models.orders import Order
        order = db.query(Order).filter(Order.id == payload.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        # Determine required hold amount (use estimated price or minimum)
        hold_amount = order.estimated_price or 100  # Minimum 1 INR in paise
        
        # Check if vehicle owner has sufficient balance
        if not check_vehicle_owner_balance(db, vehicle_owner_id, hold_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Required: {hold_amount/100} INR"
            )

        # Create the order assignment (without debiting yet)
        assignment = create_order_assignment(
            db=db,
            order_id=payload.order_id,
            vehicle_owner_id=vehicle_owner_id
        )

        db.commit()
        
        return assignment
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to accept order: {str(e)}"
        )


@router.get("/{assignment_id}", response_model=OrderAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get order assignment by ID"""
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is the vehicle owner of this assignment
    if str(assignment.vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this assignment"
        )
    
    return assignment


@router.get("/vehicle_owner/{vehicle_owner_id}", response_model=List[OrderAssignmentResponse])
async def get_assignments_by_vehicle_owner(
    vehicle_owner_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all assignments for a specific vehicle owner"""
    print(f"Vehicle owner ID: {vehicle_owner_id}")
    # Verify the authenticated user is requesting their own assignments
    if str(vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these assignments"
        )
    
    assignments = get_order_assignments_by_vehicle_owner_id(db, vehicle_owner_id)
    return assignments


@router.get("/order/{order_id}", response_model=List[OrderAssignmentResponse])
async def get_assignments_by_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all assignments for a specific order"""
    assignments = get_order_assignments_by_order_id(db, order_id)
    return assignments


@router.patch("/{assignment_id}/status", response_model=OrderAssignmentResponse)
async def update_assignment_status_endpoint(
    assignment_id: int,
    payload: OrderAssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Update assignment status"""
    # Get the assignment first to check authorization
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is the vehicle owner of this assignment
    if str(assignment.vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this assignment"
        )
    
    # Update the status
    updated_assignment = update_assignment_status(db, assignment_id, payload.assignment_status)
    if not updated_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update assignment status"
        )
    
    return updated_assignment


@router.patch("/{assignment_id}/cancel", response_model=OrderAssignmentResponse)
async def cancel_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Cancel an assignment"""
    # Get the assignment first to check authorization
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is the vehicle owner of this assignment
    if str(assignment.vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this assignment"
        )
    
    # Cancel the assignment
    cancelled_assignment = cancel_assignment(db, assignment_id)
    if not cancelled_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel assignment"
        )
    
    return cancelled_assignment


@router.patch("/{assignment_id}/complete", response_model=OrderAssignmentResponse)
async def complete_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Complete an assignment"""
    # Get the assignment first to check authorization
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is the vehicle owner of this assignment
    if str(assignment.vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to complete this assignment"
        )
    
    # Complete the assignment
    completed_assignment = complete_assignment(db, assignment_id)
    if not completed_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to complete assignment"
        )
    
@router.patch("/{assignment_id}/assign-car-driver", response_model=OrderAssignmentResponse)
async def assign_car_driver(
    assignment_id: int,
    payload: UpdateCarDriverRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Assign car and driver to an accepted order"""
    # Get the assignment first to check authorization
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if the current user is the vehicle owner of this assignment
    if str(assignment.vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this assignment"
        )
    
    # Update the assignment with car and driver
    updated_assignment = update_assignment_car_driver(
        db, 
        assignment_id, 
        str(payload.driver_id), 
        str(payload.car_id)
    )
    
    if not updated_assignment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to assign car and driver"
        )
    
    return updated_assignment


@router.get("/driver/assigned-orders", response_model=List[DriverOrderListResponse])
async def get_driver_assigned_orders_endpoint(
    db: Session = Depends(get_db),
    current_driver=Depends(get_current_driver)
):
    """Get all ASSIGNED orders for the authenticated driver"""
    driver_id = str(current_driver.id)
    assigned_orders = get_driver_assigned_orders(db, driver_id)
    return assigned_orders


@router.post("/driver/start-trip/{order_id}", response_model=StartTripResponse)
async def start_trip(
    order_id: int,
    start_km: int = Form(...),
    speedometer_img: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_driver=Depends(get_current_driver)
):
    """Start trip by uploading start KM and speedometer image"""
    try:
        # Validate image file
        if not speedometer_img.content_type or not speedometer_img.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Please upload an image file."
            )
        
        # Upload image to GCS
        from app.utils.gcs import upload_image_to_gcs
        folder_path = f"trip_records/{order_id}/start"
        speedometer_img_url = upload_image_to_gcs(speedometer_img, folder_path)
        
        # Create start trip record
        from app.crud.end_records import create_start_trip_record
        trip_record = create_start_trip_record(
            db=db,
            order_id=order_id,
            driver_id=str(current_driver.id),
            start_km=start_km,
            speedometer_img_url=speedometer_img_url
        )
        
        return {
            "message": "Trip started successfully",
            "end_record_id": trip_record.id,
            "start_km": trip_record.start_km,
            "speedometer_img_url": speedometer_img_url
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start trip: {str(e)}")


@router.post("/driver/end-trip/{order_id}", response_model=EndTripResponse)
async def end_trip(
    order_id: int,
    end_km: int = Form(...),
    toll_charge_update: bool = Form(False),
    updated_toll_charges: int | None = Form(None),
    close_speedometer_img: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_driver=Depends(get_current_driver)
):
    """End trip by uploading end KM, optional toll updates, and close speedometer image"""
    try:
        # Validate close speedometer image file
        if not close_speedometer_img.content_type or not close_speedometer_img.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Invalid close speedometer file type. Please upload an image file."
            )
        
        # Upload close speedometer image to GCS
        from app.utils.gcs import upload_image_to_gcs
        folder_path = f"trip_records/{order_id}/end"
        close_speedometer_img_url = upload_image_to_gcs(close_speedometer_img, folder_path)
        
        # Update end trip record
        from app.crud.end_records import update_end_trip_record
        result = update_end_trip_record(
            db=db,
            order_id=order_id,
            driver_id=str(current_driver.id),
            end_km=end_km,
            toll_charge_update=toll_charge_update,
            updated_toll_charges=updated_toll_charges,
            close_speedometer_image_url=close_speedometer_img_url
        )
        
        return {
            "message": "Trip ended successfully",
            "end_record_id": result["trip_record"].id,
            "end_km": result["trip_record"].end_km,
            "close_speedometer_img_url": close_speedometer_img_url,
            "total_km": result["total_km"],
            "calculated_fare": result["calculated_fare"],
            "driver_amount": result["driver_amount"],
            "vehicle_owner_amount": result["vehicle_owner_amount"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end trip: {str(e)}")


@router.get("/driver/trip-history", response_model=List[dict])
async def get_driver_trip_history(
    db: Session = Depends(get_db),
    current_driver=Depends(get_current_driver)
):
    """Get driver's trip history"""
    from app.crud.end_records import get_driver_trip_history
    driver_id = str(current_driver.id)
    trip_history = get_driver_trip_history(db, driver_id)
    return trip_history



