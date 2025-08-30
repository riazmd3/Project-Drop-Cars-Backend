from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_user, get_current_vehicleOwner_id
from app.schemas.order_assignments import (
    OrderAssignmentCreate,
    OrderAssignmentResponse,
    OrderAssignmentStatusUpdate,
    OrderAssignmentWithOrderDetails
)
from app.crud.order_assignments import (
    create_order_assignment,
    get_order_assignment_by_id,
    get_order_assignments_by_vehicle_owner_id,
    get_order_assignments_by_order_id,
    update_assignment_status,
    cancel_assignment,
    complete_assignment,
    get_vendor_orders_with_assignments
)
from app.models.order_assignments import AssignmentStatusEnum

router = APIRouter()


@router.post("/acceptorder", response_model=OrderAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def accept_order(
    payload: OrderAssignmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Accept an order and create assignment"""
    try:
        # Get vehicle_owner_id from the authenticated user
        # print("current_user", current_user)

        vehicle_owner_id = str(current_user.vehicle_owner_id)
        
        # Create the order assignment
        assignment = create_order_assignment(
            db=db,
            order_id=payload.order_id,
            vehicle_owner_id=vehicle_owner_id
        )
        
        return assignment
    except Exception as e:
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
    # Verify the authenticated user is requesting their own assignments
    if str(vehicle_owner_id) != str(current_user.vehicle_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these assignments"
        )
    
    assignments = get_order_assignments_by_vehicle_owner_id(db, vehicle_owner_id)
    return assignments


@router.get("/vehicle_owner/pending", response_model=List[OrderAssignmentWithOrderDetails])
async def get_pending_orders_for_vehicle_owner(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get pending orders for the authenticated vehicle owner based on business rules"""
    # Get vehicle_owner_id from the authenticated user
    vehicle_owner_id = str(current_user.vehicle_owner_id)
    
    from app.crud.order_assignments import get_pending_orders_for_vehicle_owner
    pending_orders = get_pending_orders_for_vehicle_owner(db, vehicle_owner_id)
    return pending_orders


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
    
    return completed_assignment


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



