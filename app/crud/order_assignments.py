from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timedelta
from app.models.order_assignments import OrderAssignment, AssignmentStatusEnum
from app.models.orders import Order


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
    
    # Calculate expiry time based on order's max_time_to_assign_order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    expires_at = order.max_time_to_assign_order or (datetime.utcnow() + timedelta(minutes=15))
    
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


def cancel_timed_out_pending_assignments(db: Session) -> int:
    """Cancel PENDING assignments that exceeded order's max_time_to_assign_order and have no driver/car assigned.

    Returns number of assignments cancelled in this run.
    """
    now = datetime.utcnow()
    # Find pending assignments whose order's max_time_to_assign_order has passed
    pending_assignments = (
        db.query(OrderAssignment)
        .join(Order, Order.id == OrderAssignment.order_id)
        .filter(
            OrderAssignment.assignment_status == AssignmentStatusEnum.PENDING,
            OrderAssignment.driver_id.is_(None),
            OrderAssignment.car_id.is_(None),
            Order.max_time_to_assign_order <= now
        )
        .all()
    )

    cancelled_count = 0
    for assignment in pending_assignments:
        assignment.assignment_status = AssignmentStatusEnum.CANCELLED
        assignment.cancelled_at = now
        cancelled_count += 1

    if cancelled_count:
        db.commit()

    return cancelled_count


def get_order_assignment_by_id(db: Session, assignment_id: int) -> Optional[OrderAssignment]:
    """Get order assignment by ID"""
    return db.query(OrderAssignment).filter(OrderAssignment.id == assignment_id).first()


def get_order_assignments_by_vehicle_owner_id(db: Session, vehicle_owner_id: str) -> List[OrderAssignment]:
    """Get all order assignments for a specific vehicle owner"""
    # print(f"Vehicle owner ID: {vehicle_owner_id}")
    return db.query(OrderAssignment).filter(
        OrderAssignment.vehicle_owner_id == vehicle_owner_id,
        OrderAssignment.assignment_status.in_([AssignmentStatusEnum.ASSIGNED, AssignmentStatusEnum.PENDING])
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
    orders = db.query(Order).filter(Order.vendor_id == vendor_id).all()
    
    result = []
    for order in orders:
        # Get the latest assignment for this order
        latest_assignment = db.query(OrderAssignment).filter(
            OrderAssignment.order_id == order.id
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
    1. Orders that are not in assignment table (never assigned)
    2. Orders that are cancelled in assignment table (latest assignment status is CANCELLED)
    3. Orders with trip_status != "CANCELLED" (exclude cancelled orders)
    
    Business Logic:
    - Compare orders table with order_assignments table
    - For each order, get the latest assignment record (most recent created_at)
    - If no assignment exists, order is available
    - If latest assignment is CANCELLED, order is available for reassignment
    - If latest assignment is active (PENDING, ASSIGNED, COMPLETED, DRIVING), order is not available
    """
    from sqlalchemy import and_, or_, not_, desc
    
    # Get all orders excluding cancelled ones
    all_orders = db.query(Order).filter(Order.trip_status != "CANCELLED").all()
    pending_orders = []
    
    for order in all_orders:
        # Get the latest assignment for this order (most recent created_at)
        # This ensures we compare with the most recent assignment status
        latest_assignment = db.query(OrderAssignment).filter(
            OrderAssignment.order_id == order.id
        ).order_by(desc(OrderAssignment.created_at)).first()
        
        if not latest_assignment:
            # Rule 1: Order not in assignment table - should be available
            pending_orders.append({
                # "id": None,  # No assignment ID
                "order_id": order.id,
                "vehicle_owner_id": vehicle_owner_id,
                # "driver_id": None,
                # "car_id": None,
                "assignment_status": AssignmentStatusEnum.PENDING,
                # "assigned_at": None,
                # "expires_at": None,
                # "cancelled_at": None,
                # "completed_at": None,
                "created_at": order.created_at or datetime.utcnow(),  # Fallback to current time if None
                # Order details
                "vendor_id": order.vendor_id,
                "trip_type": order.trip_type.value if order.trip_type else "Unknown",
                "car_type": order.car_type.value if order.car_type else "Unknown",
                "pickup_drop_location": order.pickup_drop_location or {},
                "start_date_time": order.start_date_time or datetime.utcnow(),
                "customer_name": order.customer_name or "Unknown",
                "customer_number": order.customer_number or "Unknown",
                # "cost_per_km": 0,  # Orders table doesn't have these fields
                # "extra_cost_per_km": 0,
                # "driver_allowance": 0,
                # "extra_driver_allowance": 0,
                # "permit_charges": 0,
                # "extra_permit_charges": 0,
                # "hill_charges": 0,
                # "vendor_price": order.vendor_price,
                # "driver_price": order.estimated_price,
                "pickup_notes": None,
                "trip_status": order.trip_status or "Unknown",
                "pick_near_city": order.pick_near_city or "Unknown",
                "trip_distance": order.trip_distance or 0,
                "trip_time": order.trip_time or "Unknown",
                "platform_fees_percent": order.platform_fees_percent or 0,
                "estimated_price": order.estimated_price,
                "vendor_price": order.vendor_price,
                "order_created_at": order.created_at or datetime.utcnow()
            })
        # elif latest_assignment.assignment_status == AssignmentStatusEnum.CANCELLED:
        #     # Rule 2: Order is cancelled in assignment table - should be available
        #     pending_orders.append({
        #         "id": latest_assignment.id,
        #         "order_id": order.id,
        #         "vehicle_owner_id": vehicle_owner_id,
        #         "driver_id": latest_assignment.driver_id,
        #         "car_id": latest_assignment.car_id,
        #         "assignment_status": AssignmentStatusEnum.PENDING,  # Show as pending for new assignment
        #         "assigned_at": latest_assignment.assigned_at,
        #         "expires_at": latest_assignment.expires_at,
        #         "cancelled_at": latest_assignment.cancelled_at,
        #         "completed_at": latest_assignment.completed_at,
        #         "created_at": latest_assignment.created_at or datetime.utcnow(),
        #         # Order details
        #         "vendor_id": order.vendor_id,
        #         "trip_type": order.trip_type.value if order.trip_type else "Unknown",
        #         "car_type": order.car_type.value if order.car_type else "Unknown",
        #         "pickup_drop_location": order.pickup_drop_location or {},
        #         "start_date_time": order.start_date_time or datetime.utcnow(),
        #         "customer_name": order.customer_name or "Unknown",
        #         "customer_number": order.customer_number or "Unknown",
        #         "cost_per_km": 0,  # Orders table doesn't have these fields
        #         "extra_cost_per_km": 0,
        #         "driver_allowance": 0,
        #         "extra_driver_allowance": 0,
        #         "permit_charges": 0,
        #         "extra_permit_charges": 0,
        #         "hill_charges": 0,
        #         "toll_charges": 0,
        #         "pickup_notes": None,
        #         "trip_status": order.trip_status or "Unknown",
        #         "pick_near_city": order.pick_near_city or "Unknown",
        #         "trip_distance": order.trip_distance or 0,
        #         "trip_time": order.trip_time or "Unknown",
        #         "platform_fees_percent": order.platform_fees_percent or 0,
        #         "estimated_price": order.estimated_price,
        #         "vendor_price": order.vendor_price,
        #         "order_created_at": order.created_at or datetime.utcnow()
        #     })
        # Note: Orders with active assignments (PENDING, ASSIGNED, COMPLETED, DRIVING) are NOT included
        # as they are not available for new assignments
    
    return pending_orders

def update_assignment_car_driver(
    db: Session, 
    assignment_id: int, 
    driver_id: str, 
    car_id: str
) -> Optional[OrderAssignment]:
    """Update assignment with driver and car"""
    assignment = get_order_assignment_by_id(db, assignment_id)
    if not assignment:
        return None
    
    assignment.driver_id = driver_id
    assignment.car_id = car_id
    assignment.assignment_status = AssignmentStatusEnum.ASSIGNED
    assignment.assigned_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assignment)
    return assignment

def get_driver_assigned_orders(db: Session, driver_id: str) -> List[dict]:
    """Get all ASSIGNED orders for a specific driver"""
    assignments = db.query(OrderAssignment).filter(
        OrderAssignment.driver_id == driver_id,
        # OrderAssignment.assignment_status == AssignmentStatusEnum.ASSIGNED
        OrderAssignment.assignment_status.in_([AssignmentStatusEnum.ASSIGNED, AssignmentStatusEnum.DRIVING])
    ).order_by(desc(OrderAssignment.assigned_at)).all()
    
    result = []
    for assignment in assignments:
        # Get order details
        order = db.query(Order).filter(Order.id == assignment.order_id).first()
        if order:
            result.append({
                "id": assignment.id,
                "order_id": assignment.order_id,
                "assignment_status": assignment.assignment_status,
                "customer_name": order.customer_name,
                "customer_number": order.customer_number,
                "pickup_drop_location": order.pickup_drop_location,
                "start_date_time": order.start_date_time,
                "trip_type": order.trip_type.value if order.trip_type else "Unknown",
                "car_type": order.car_type.value if order.car_type else "Unknown",
                "estimated_price": order.estimated_price,
                "assigned_at": assignment.assigned_at,
                "created_at": assignment.created_at
            })
    
    return result

def check_vehicle_owner_balance(db: Session, vehicle_owner_id: str, required_amount: int) -> bool:
    """Check if vehicle owner has sufficient balance"""
    from app.crud.wallet import get_owner_balance
    try:
        balance = get_owner_balance(db, vehicle_owner_id)
        return balance >= required_amount
    except:
        return False
