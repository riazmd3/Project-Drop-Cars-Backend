from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.models.end_records import EndRecord
from app.models.order_assignments import OrderAssignment, AssignmentStatusEnum
from app.models.orders import Order
from app.models.car_driver import CarDriver, AccountStatusEnum

def create_start_trip_record(
    db: Session,
    order_id: int,
    driver_id: str,
    start_km: int,
    speedometer_img_url: str
) -> EndRecord:
    """Create start trip record"""
    # Check if driver is assigned to this order
    assignment = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.driver_id == driver_id,
        OrderAssignment.assignment_status == AssignmentStatusEnum.ASSIGNED
    ).first()
    
    if not assignment:
        raise ValueError("Driver is not assigned to this order")
    
    # Check if trip already started
    existing_record = db.query(EndRecord).filter(
        EndRecord.order_id == order_id,
        EndRecord.driver_id == driver_id
    ).first()
    
    if existing_record:
        raise ValueError("Trip already started for this order")
    
    # Create start trip record
    trip_record = EndRecord(
        order_id=order_id,
        driver_id=driver_id,
        start_km=start_km,
        end_km=0,  # Will be updated when trip ends
        contact_number="",  # Will be updated when trip ends
        img_url=speedometer_img_url
    )
    
    db.add(trip_record)
    db.commit()
    db.refresh(trip_record)
    
    # Update assignment status to DRIVING
    assignment.assignment_status = AssignmentStatusEnum.DRIVING
    db.commit()
    
    # Update driver status to DRIVING
    driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()
    if driver:
        driver.driver_status = AccountStatusEnum.DRIVING
        db.commit()
    
    return trip_record

def update_end_trip_record(
    db: Session,
    order_id: int,
    driver_id: str,
    end_km: int,
    speedometer_img_url: str,
    contact_number: str,
    close_speedometer_image_url: str = None
) -> dict:
    """Update end trip record and calculate fare"""
    # Get the trip record
    trip_record = db.query(EndRecord).filter(
        EndRecord.order_id == order_id,
        EndRecord.driver_id == driver_id
    ).first()
    
    if not trip_record:
        raise ValueError("Trip record not found")
    
    if trip_record.end_km > 0:
        raise ValueError("Trip already ended")
    
    # Update trip record
    trip_record.end_km = end_km
    trip_record.contact_number = contact_number
    trip_record.img_url = speedometer_img_url  # Update with end image
    trip_record.close_speedometer_image = close_speedometer_image_url  # Add close speedometer image
    
    # Calculate fare
    total_km = end_km - trip_record.start_km
    if total_km < 0:
        raise ValueError("End KM cannot be less than start KM")
    
    # Get order details for fare calculation
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    
    # Calculate fare based on order pricing
    # Note: Orders table doesn't have detailed pricing, using estimated_price
    base_fare = order.estimated_price or 0
    calculated_fare = base_fare
    
    # Update order with final amounts and status
    order.closed_vendor_price = calculated_fare
    order.closed_driver_price = int(calculated_fare * 0.7)  # 70% to driver
    order.commision_amount = int(calculated_fare * 0.3)  # 30% commission
    order.trip_status = "COMPLETED"  # Update order status to completed
    
    # Get assignment to find vehicle owner
    assignment = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.driver_id == driver_id
    ).first()
    
    if assignment:
        # Debit amount from vehicle owner
        from app.crud.wallet import debit_wallet
        from app.models.wallet_ledger import WalletEntryTypeEnum
        
        try:
            debit_wallet(
                db,
                vehicle_owner_id=str(assignment.vehicle_owner_id),
                amount=calculated_fare,
                reference_id=str(order_id),
                reference_type="TRIP_COMPLETION",
                notes=f"Trip completion - {total_km} km"
            )
        except ValueError as e:
            raise ValueError(f"Wallet debit failed: {str(e)}")
        
        # Update assignment status to COMPLETED
        assignment.assignment_status = AssignmentStatusEnum.COMPLETED
        assignment.completed_at = datetime.utcnow()
    
    # Update driver status back to ONLINE
    driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()
    if driver:
        driver.driver_status = AccountStatusEnum.ONLINE
        db.commit()
    
    db.commit()
    db.refresh(trip_record)
    
    return {
        "trip_record": trip_record,
        "total_km": total_km,
        "calculated_fare": calculated_fare,
        "driver_amount": int(calculated_fare * 0.7),
        "vehicle_owner_amount": int(calculated_fare * 0.3)
    }

def get_driver_trip_history(db: Session, driver_id: str) -> List[dict]:
    """Get driver's trip history"""
    trip_records = db.query(EndRecord).filter(
        EndRecord.driver_id == driver_id,
        EndRecord.end_km > 0  # Only completed trips
    ).order_by(EndRecord.created_at.desc()).all()
    
    result = []
    for record in trip_records:
        # Get order details
        order = db.query(Order).filter(Order.id == record.order_id).first()
        if order:
            total_km = record.end_km - record.start_km
            result.append({
                "id": record.id,
                "order_id": record.order_id,
                "customer_name": order.customer_name,
                "customer_number": order.customer_number,
                "start_km": record.start_km,
                "end_km": record.end_km,
                "total_km": total_km,
                "contact_number": record.contact_number,
                "img_url": record.img_url,
                "created_at": record.created_at,
                "trip_type": order.trip_type.value if order.trip_type else "Unknown",
                "estimated_price": order.estimated_price
            })
    
    return result
