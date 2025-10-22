from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.models.end_records import EndRecord
from app.models.order_assignments import OrderAssignment, AssignmentStatusEnum
from app.models.orders import Order
from app.models.new_orders import NewOrder
from app.models.hourly_rental import HourlyRental
from app.models.car_driver import CarDriver, AccountStatusEnum
from app.crud.notification import send_trip_status_notification_to_vendor_and_vehicle_owner
async def create_start_trip_record(
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
    await send_trip_status_notification_to_vendor_and_vehicle_owner(db, order_id=order_id, status="started")
    return trip_record

async def update_end_trip_record(
    db: Session,
    order_id: int,
    driver_id: str,
    end_km: int,
    *,
    # toll_charge_update: bool = False,
    updated_toll_charges: int | None = None,
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
    # print("Hello")
    # Update trip record
    trip_record.end_km = end_km
    trip_record.close_speedometer_image = close_speedometer_image_url  # Add close speedometer image
    
    # Calculate fare
    total_km = end_km - trip_record.start_km
    if total_km < 0:
        raise ValueError("End KM cannot be less than start KM")
    # Ensure difference km is greater than original planned km (when available)
    if order := db.query(Order).filter(Order.id == order_id).first():
        # For all trip types, enforce updated km > old km when order.trip_distance exists
        if order.trip_distance is not None and total_km <= int(order.trip_distance):
            raise ValueError("Updated total KM must be greater than the original trip distance")
    
    # Get order details for fare calculation
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    
    if order.toll_charge_update == True:
        # print("Toll charge update already applied, cannot update again",order.toll_charge_update)
        if updated_toll_charges is  None or not(updated_toll_charges > 10):
            raise ValueError("You Must Enter the Toll charges for this order")
    
    # Calculate fare based on order pricing
    calculated_fare = order.estimated_price or 0
    # admin_commission = 0
    if order.source and order.source.name == "HOURLY_RENTAL":
        # Fetch hourly rental pricing data
        hourly = db.query(HourlyRental).filter(HourlyRental.id == order.source_order_id).first()
        if not hourly:
            raise ValueError("Hourly rental source order not found")

        hours_selected = int(hourly.package_hours.get("hours", 0))
        included_km_range = int(hourly.package_hours.get("km_range", 0))
        balance_km = max(0, int(total_km) - included_km_range)

        vendor_total = (
            (int(hourly.cost_per_hour) + int(hourly.extra_cost_per_hour)) * hours_selected
        ) + (
            balance_km * (int(hourly.cost_for_addon_km) + int(hourly.extra_cost_for_addon_km))
        )

        estimated_total = (
            int(hourly.cost_per_hour) * hours_selected
        ) + (
            balance_km * int(hourly.cost_for_addon_km)
        )

        # Apply toll charge updates equally if provided
        if order.toll_charge_update and updated_toll_charges is not None:
            estimated_total += int(updated_toll_charges)
            vendor_total += int(updated_toll_charges)
        elif order.toll_charge_update and updated_toll_charges is None:
            # If update flag is true but value missing, block
            raise ValueError("Updated toll charges must be provided when toll_charge_update is true")

        # Admin profit: 10% of (vendor - estimate)
        diff = max(0, int(vendor_total) - int(estimated_total))
        admin_commission = int(round(diff * 0.10))

        calculated_fare = int(vendor_total)
    else:
        # Note: Orders table doesn't have detailed pricing, using estimated_price for non-hourly
        base_fare = order.estimated_price or 0
        calculated_fare = base_fare

    # Apply toll updates if provided
    if order.toll_charge_update == True:
        # order.toll_charge_update = True
        if updated_toll_charges is not None:
            order.updated_toll_charges = updated_toll_charges
            if not (order.source and order.source.name == "HOURLY_RENTAL"):
                calculated_fare = (order.estimated_price or 0) + updated_toll_charges
        else:
            # Missing toll charges when flag is true
            raise ValueError("Updated toll charges must be provided when toll_charge_update is true")
    else:
        # order.toll_charge_update = False
        order.updated_toll_charges = None
    
    # Update order with final amounts, profits, and status

    # order.closed_vendor_price = int(calculated_fare)
    if order.source and order.source.name == "HOURLY_RENTAL":
        # Reuse estimated_total/vendor_total from hourly branch
        # Vendor profit per spec: (vendor_total - estimated_total) + 10% of (cost_per_km * updated_km)
        hours_selected = int(hourly.package_hours.get("hours", 0))
        included_km_range = int(hourly.package_hours.get("km_range", 0))


        balance_km = max(0, int(total_km) - included_km_range)
        # extra_vendor_component = int(round((int(hourly.cost_for_addon_km) * int(total_km)) * 0.10))
        # vendor_profit = max(0, int(vendor_total) - int(estimated_total)) + extra_vendor_component

        # admin_profit = int(round(vendor_profit * 0.10))
        # # Driver profit is the remainder from estimated side as per spec
        # driver_profit = max(0, int(estimated_total) - admin_profit)

        commision_amount = 10
        cal_driver_price = (hourly.cost_per_hour * hours_selected) + (balance_km * hourly.cost_for_addon_km)
        cal_vendor_price = ((hourly.cost_per_hour + hourly.extra_cost_per_hour) * hours_selected) + (balance_km * (hourly.cost_for_addon_km + hourly.extra_cost_for_addon_km))

        cal_vendor_profit = (cal_vendor_price - cal_driver_price)
        cal_admin_profit = cal_vendor_profit * (commision_amount/100)


        order.closed_vendor_price = cal_vendor_price
        order.closed_driver_price = cal_driver_price

        order.vendor_profit = cal_vendor_profit - cal_admin_profit
        order.admin_profit = cal_admin_profit
        order.driver_profit = cal_vendor_price - cal_vendor_profit
        order.commision_amount = commision_amount
    else:

        #New Custom Verification
        new_order = db.query(NewOrder).filter(NewOrder.order_id == order.source_order_id).first()
        if not new_order:
            raise ValueError("New order not found")
        cost_per_km = new_order.cost_per_km
        extra_cost_per_km = new_order.extra_cost_per_km
        driver_allowance = new_order.driver_allowance
        extra_driver_allowance = new_order.extra_driver_allowance
        permit_charges = new_order.permit_charges
        extra_permit_charges = new_order.extra_permit_charges
        hill_charges = new_order.hill_charges
        toll_charges = order.updated_toll_charges if order.updated_toll_charges else new_order.toll_charges
        updated_km = total_km

        closed_vendor_price = ((cost_per_km+extra_cost_per_km)*updated_km) + (driver_allowance+extra_driver_allowance) + (permit_charges+extra_permit_charges) + (hill_charges) + (toll_charges)
        closed_driver_price = ((cost_per_km)*updated_km) + (driver_allowance) + (permit_charges) + (hill_charges) + (toll_charges)
        commision_amount = 10
        vendor_amount_to_receive_from_driver = closed_vendor_price - closed_driver_price + ((cost_per_km*updated_km)*(commision_amount/100))
        vendor_profit = vendor_amount_to_receive_from_driver - (vendor_amount_to_receive_from_driver*(commision_amount/100))
        admin_profit = vendor_amount_to_receive_from_driver*(commision_amount/100)
        driver_profit = closed_vendor_price - vendor_amount_to_receive_from_driver

        #New Custom Verification
        # For non-hourly, keep existing behavior but set profits coherently
        print("Calculated fare", calculated_fare)
        print("Estimated price", order.estimated_price)
        # print()
        order.closed_vendor_price = closed_vendor_price
        order.vendor_profit = vendor_profit
        order.admin_profit = admin_profit
        order.driver_profit = driver_profit
        order.closed_driver_price = closed_driver_price
        order.commision_amount = commision_amount
        print("Admin profit", admin_profit)
        print("Driver profit", driver_profit)
        print("Vendor profit", vendor_profit)
    order.trip_status = "COMPLETED"  # Update order status to completed
    
    # Get assignment to find vehicle owner
    assignment = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.driver_id == driver_id
    ).first()
    
    if assignment:
        # Debit amount from vehicle owner
        from app.crud.wallet import debit_wallet
        from app.crud.vendor_wallet import credit_vendor_wallet
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
        # Credit vendor wallet with vendor_profit via vendor ledger
        try:
            credit_vendor_wallet(
                db,
                vendor_id=str(order.vendor_id),
                amount=int(order.vendor_profit or 0),
                order_id=order_id,
                notes=f"Trip {order_id} vendor profit"
            )
        except ValueError as e:
            raise ValueError(f"Vendor wallet credit failed: {str(e)}")
        
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
    await send_trip_status_notification_to_vendor_and_vehicle_owner(db, order_id=17, status="ended")
    return {
        "trip_record": trip_record,
        "total_km": total_km,
        # "calculated_fare": calculated_fare,
        # "driver_amount": int(calculated_fare * 0.7),
        # "vehicle_owner_amount": int(calculated_fare * 0.3)
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
