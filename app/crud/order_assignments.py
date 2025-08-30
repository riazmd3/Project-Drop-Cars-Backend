from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from app.models.order_assignments import OrderAssignment, AssignmentStatusEnum
from app.models.new_orders import NewOrder


def create_order_assignment(
    db: Session, 
    order_id: int, 
    vehicle_owner_id: str
) -> OrderAssignment:
    """Create a new order assignment"""
    # Check if order already has an active assignment (not cancelled)
    existing_assignment = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.assignment_status != AssignmentStatusEnum.CANCELLED
    ).first()
    
    if existing_assignment:
        raise ValueError(f"Order {order_id} already has an active assignment with status {existing_assignment.assignment_status}")
    
    # Calculate expiry time (1 hour from now)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    db_assignment = OrderAssignment(
        order_id=order_id,
        vehicle_owner_id=vehicle_owner_id,
        assignment_status=AssignmentStatusEnum.PENDING,
        expires_at=expires_at,
        created_at=datetime.utcnow()
    )
    
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def get_order_assignment_by_id(db: Session, assignment_id: int) -> Optional[OrderAssignment]:
    """Get order assignment by ID"""
    return db.query(OrderAssignment).filter(OrderAssignment.id == assignment_id).first()


def get_order_assignments_by_vehicle_owner_id(db: Session, vehicle_owner_id: str) -> List[OrderAssignment]:
    """Get all order assignments for a specific vehicle owner"""
    return db.query(OrderAssignment).filter(
        OrderAssignment.vehicle_owner_id == vehicle_owner_id
    ).order_by(desc(OrderAssignment.created_at)).all()


def get_order_assignments_by_order_id(db: Session, order_id: int) -> List[OrderAssignment]:
    """Get all order assignments for a specific order"""
    return db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id
    ).order_by(desc(OrderAssignment.created_at)).all()


def update_assignment_status(
    db: Session, 
    assignment_id: int, 
    new_status: AssignmentStatusEnum
) -> Optional[OrderAssignment]:
    """Update assignment status and related timestamps"""
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        return None
    
    assignment.assignment_status = new_status
    
    # Update timestamps based on status
    if new_status == AssignmentStatusEnum.ASSIGNED:
        assignment.assigned_at = datetime.utcnow()
    elif new_status == AssignmentStatusEnum.CANCELLED:
        assignment.cancelled_at = datetime.utcnow()
    elif new_status == AssignmentStatusEnum.COMPLETED:
        assignment.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    return assignment


def cancel_assignment(db: Session, assignment_id: int) -> Optional[OrderAssignment]:
    """Cancel an assignment"""
    return update_assignment_status(db, assignment_id, AssignmentStatusEnum.CANCELLED)


def complete_assignment(db: Session, assignment_id: int) -> Optional[OrderAssignment]:
    """Complete an assignment"""
    return update_assignment_status(db, assignment_id, AssignmentStatusEnum.COMPLETED)


def get_vendor_orders_with_assignments(db: Session, vendor_id: str) -> List[dict]:
    """Get all orders for a vendor with their latest assignment details"""
    # Get all orders for the vendor
    print("vendor_id......", vendor_id)
    orders = db.query(NewOrder).filter(NewOrder.vendor_id == vendor_id).all()
    
    result = []
    for order in orders:
        # Get the latest assignment for this order
        latest_assignment = db.query(OrderAssignment).filter(
            OrderAssignment.order_id == order.order_id
        ).order_by(desc(OrderAssignment.created_at)).first()
        
        if latest_assignment:
            # Combine order and assignment data
            order_data = {
                # Order assignment details
                "id": latest_assignment.id,
                "order_id": latest_assignment.order_id,
                "vehicle_owner_id": latest_assignment.vehicle_owner_id,
                "driver_id": latest_assignment.driver_id,
                "car_id": latest_assignment.car_id,
                "assignment_status": latest_assignment.assignment_status,
                "assigned_at": latest_assignment.assigned_at,
                "expires_at": latest_assignment.expires_at,
                "cancelled_at": latest_assignment.cancelled_at,
                "completed_at": latest_assignment.completed_at,
                "created_at": latest_assignment.created_at,
                
                # Order details
                "vendor_id": order.vendor_id,
                "trip_type": order.trip_type.value,
                "car_type": order.car_type.value,
                "pickup_drop_location": order.pickup_drop_location,
                "start_date_time": order.start_date_time,
                "customer_name": order.customer_name,
                "customer_number": order.customer_number,
                "cost_per_km": order.cost_per_km,
                "extra_cost_per_km": order.extra_cost_per_km,
                "driver_allowance": order.driver_allowance,
                "extra_driver_allowance": order.extra_driver_allowance,
                "permit_charges": order.permit_charges,
                "extra_permit_charges": order.extra_permit_charges,
                "hill_charges": order.hill_charges,
                "toll_charges": order.toll_charges,
                "pickup_notes": order.pickup_notes,
                "trip_status": order.trip_status,
                "pick_near_city": order.pick_near_city,
                "trip_distance": order.trip_distance,
                "trip_time": order.trip_time,
                "platform_fees_percent": order.platform_fees_percent,
                "estimated_price": order.estimated_price,
                "vendor_price": order.vendor_price,
                "order_created_at": order.created_at
            }
            result.append(order_data)
    
    return result


def get_pending_orders_for_vehicle_owner(db: Session, vehicle_owner_id: str) -> List[dict]:
    """
    Get pending orders for a vehicle owner based on business rules:
    1. Orders that are not in assignment table
    2. Orders that are cancelled in assignment table
    """
    from sqlalchemy import and_, or_, not_
    
    # Get all orders
    all_orders = db.query(NewOrder).all()
    pending_orders = []
    
    for order in all_orders:
        # Check if order exists in assignment table
        existing_assignment = db.query(OrderAssignment).filter(
            OrderAssignment.order_id == order.order_id
        ).first()
        
        if not existing_assignment:
            # Rule 1: Order not in assignment table - should be available
            pending_orders.append({
                "id": None,  # No assignment ID
                "order_id": order.order_id,
                "vehicle_owner_id": vehicle_owner_id,
                "driver_id": None,
                "car_id": None,
                "assignment_status": AssignmentStatusEnum.PENDING,
                "assigned_at": None,
                "expires_at": None,
                "cancelled_at": None,
                "completed_at": None,
                "created_at": order.created_at,
                # Order details
                "vendor_id": order.vendor_id,
                "trip_type": order.trip_type.value,
                "car_type": order.car_type.value,
                "pickup_drop_location": order.pickup_drop_location,
                "start_date_time": order.start_date_time,
                "customer_name": order.customer_name,
                "customer_number": order.customer_number,
                "cost_per_km": order.cost_per_km,
                "extra_cost_per_km": order.extra_cost_per_km,
                "driver_allowance": order.driver_allowance,
                "extra_driver_allowance": order.extra_driver_allowance,
                "permit_charges": order.permit_charges,
                "extra_permit_charges": order.extra_permit_charges,
                "hill_charges": order.hill_charges,
                "toll_charges": order.toll_charges,
                "pickup_notes": order.pickup_notes,
                "trip_status": order.trip_status,
                "pick_near_city": order.pick_near_city,
                "trip_distance": order.trip_distance,
                "trip_time": order.trip_time,
                "platform_fees_percent": order.platform_fees_percent,
                "estimated_price": order.estimated_price,
                "vendor_price": order.vendor_price,
                "order_created_at": order.created_at
            })
        elif existing_assignment.assignment_status == AssignmentStatusEnum.CANCELLED:
            # Rule 2: Order is cancelled in assignment table - should be available
            pending_orders.append({
                "id": existing_assignment.id,
                "order_id": order.order_id,
                "vehicle_owner_id": vehicle_owner_id,
                "driver_id": existing_assignment.driver_id,
                "car_id": existing_assignment.car_id,
                "assignment_status": AssignmentStatusEnum.PENDING,  # Show as pending for new assignment
                "assigned_at": existing_assignment.assigned_at,
                "expires_at": existing_assignment.expires_at,
                "cancelled_at": existing_assignment.cancelled_at,
                "completed_at": existing_assignment.completed_at,
                "created_at": existing_assignment.created_at,
                # Order details
                "vendor_id": order.vendor_id,
                "trip_type": order.trip_type.value,
                "car_type": order.car_type.value,
                "pickup_drop_location": order.pickup_drop_location,
                "start_date_time": order.start_date_time,
                "customer_name": order.customer_name,
                "customer_number": order.customer_number,
                "cost_per_km": order.cost_per_km,
                "extra_cost_per_km": order.extra_cost_per_km,
                "driver_allowance": order.driver_allowance,
                "extra_driver_allowance": order.extra_driver_allowance,
                "permit_charges": order.permit_charges,
                "extra_permit_charges": order.extra_permit_charges,
                "hill_charges": order.hill_charges,
                "toll_charges": order.toll_charges,
                "pickup_notes": order.pickup_notes,
                "trip_status": order.trip_status,
                "pick_near_city": order.pick_near_city,
                "trip_distance": order.trip_distance,
                "trip_time": order.trip_time,
                "platform_fees_percent": order.platform_fees_percent,
                "estimated_price": order.estimated_price,
                "vendor_price": order.vendor_price,
                "order_created_at": order.created_at
            })
    
    return pending_orders
