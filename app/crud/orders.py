from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta
from sqlalchemy import func, extract

from app.models.orders import Order, OrderSourceEnum
from app.models.end_records import EndRecord
from app.utils.gcs import upload_image_to_gcs
from app.models.new_orders import NewOrder, OrderTypeEnum
from app.models.hourly_rental import HourlyRental
from app.models.order_assignments import OrderAssignment,AssignmentStatusEnum
from sqlalchemy.sql import or_, and_
from app.crud.notification import send_push_notifications_vehicle_owner
import asyncio


def create_master_from_new_order(db: Session, new_order: NewOrder, max_time_to_assign_order: int = 15, toll_charge_update: bool = False) -> Order:
    master = Order(
        source=OrderSourceEnum.NEW_ORDERS,
        source_order_id=new_order.order_id,
        vendor_id=new_order.vendor_id,
        trip_type=new_order.trip_type,
        car_type=new_order.car_type,
        pickup_drop_location=new_order.pickup_drop_location,
        start_date_time=new_order.start_date_time,
        customer_name=new_order.customer_name,
        customer_number=new_order.customer_number,
        trip_status=new_order.trip_status,
        pick_near_city=new_order.pick_near_city,
        trip_distance=new_order.trip_distance,
        trip_time=new_order.trip_time,
        estimated_price=new_order.estimated_price,
        vendor_price=new_order.vendor_price,
        platform_fees_percent=new_order.platform_fees_percent,
        max_time_to_assign_order=(datetime.utcnow() + timedelta(minutes=max_time_to_assign_order)),
        toll_charge_update=toll_charge_update
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    asyncio.ensure_future(
        send_push_notifications_vehicle_owner(db, f"New Order Alert ({new_order.trip_type.value})", f"A new order has been Received (ID: {master.id})")
    )
    return master


def create_master_from_hourly(db: Session, hourly: HourlyRental, *, pick_near_city: str, trip_time : int, estimated_price: int, vendor_price:int, max_time_to_assign_order: int = 15, toll_charge_update: bool = False) -> Order:
    master = Order(
        source=OrderSourceEnum.HOURLY_RENTAL,
        source_order_id=hourly.id,
        vendor_id=hourly.vendor_id,
        trip_type=hourly.trip_type,
        car_type=hourly.car_type,
        pickup_drop_location=hourly.pickup_drop_location,
        start_date_time=hourly.start_date_time,
        customer_name=hourly.customer_name,
        customer_number=hourly.customer_number,
        trip_status="PENDING",
        pick_near_city=pick_near_city,
        trip_time = trip_time,
        estimated_price = int(estimated_price),
        vendor_price = int(vendor_price),
        platform_fees_percent = 10,
        trip_distance = hourly.package_hours['km_range'],
        max_time_to_assign_order=(datetime.utcnow() + timedelta(minutes=max_time_to_assign_order)),
        toll_charge_update=toll_charge_update
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    asyncio.ensure_future(
        send_push_notifications_vehicle_owner(db, "Hourly Rental Alert (Hourly Rental)", f"A new order has been Received (ID: {master.id}) is created.")
    )
    return master


def get_all_orders(db: Session) -> List[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).all()


def set_vehicle_owner_visibility(db: Session, order_id: int, vendor_id: str, visible: bool) -> Order:
    """Toggle vehicle owner visibility for customer data, ensuring vendor ownership."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")
    if str(order.vendor_id) != str(vendor_id):
        raise ValueError("Not authorized to modify this order")
    if order.data_visibility_vehicle_owner:
        order.data_visibility_vehicle_owner = not order.data_visibility_vehicle_owner
    else:
        order.data_visibility_vehicle_owner = bool(visible)    
    db.commit()
    db.refresh(order)
    return order


# def get_vendor_orders(db: Session, vendor_id: str) -> List[Order]:
#     print("Vendor ID in CRUD:", vendor_id)
#     return db.query(Order).filter(Order.vendor_id == vendor_id).order_by(Order.created_at.desc()).all()


def map_to_combined_schema(order, new_order=None, hourly_rental=None):
    # Calculate max_time in minutes
    max_time = None
    if order.max_time_to_assign_order and order.created_at:
        time_diff = (order.max_time_to_assign_order - order.created_at).total_seconds() / 60
        max_time = int(time_diff)
    
    # BaseOrderSchema fields
    base_data = {
        "id": order.id,
        "source": order.source.value,  # enum as string
        "source_order_id": order.source_order_id,
        "vendor_id": order.vendor_id,  # UUID, ensure correct type
        "trip_type": order.trip_type.value,
        "car_type": order.car_type.value,
        "pickup_drop_location": order.pickup_drop_location,
        "start_date_time": order.start_date_time,
        "customer_name": order.customer_name,
        "customer_number": order.customer_number,
        "trip_status": order.trip_status,
        "pick_near_city": order.pick_near_city,
        "trip_distance": order.trip_distance,
        "trip_time": order.trip_time,
        "estimated_price": order.estimated_price,
        "vendor_price": order.vendor_price,
        "platform_fees_percent": order.platform_fees_percent,
        "closed_vendor_price": order.closed_vendor_price,
        "closed_driver_price": order.closed_driver_price,
        "commision_amount": order.commision_amount,
        "created_at": order.created_at,
        "max_time": max_time,
        "cancelled_by" : order.cancelled_by,
        "h_cost_for_addon_km": hourly_rental.cost_for_addon_km if hourly_rental else None,
        "h_extra_cost_for_addon_km": hourly_rental.extra_cost_for_addon_km if hourly_rental else None,
        "cost_per_km" : new_order.cost_per_km if new_order else None,
        "venodr_profit" : order.vendor_profit if order else None,
        "admin_profit" : order.admin_profit if order else None,
    }
    print("Base Data:", base_data)

    # source_data based on source type
    if order.source == OrderSourceEnum.NEW_ORDERS and new_order:
        source_data = {
            "order_id": new_order.order_id,
            "cost_per_km": new_order.cost_per_km,
            "extra_cost_per_km": new_order.extra_cost_per_km,
            "driver_allowance": new_order.driver_allowance,
            "extra_driver_allowance": new_order.extra_driver_allowance,
            "permit_charges": new_order.permit_charges,
            "extra_permit_charges": new_order.extra_permit_charges,
            "hill_charges": new_order.hill_charges,
            "toll_charges": new_order.toll_charges,
            "pickup_notes": new_order.pickup_notes,
            # "cost_per_km" : order.cost_per_km if hasattr(order, 'cost_per_km') else None,
            # "venodr_profit" : order.vendor_profit if order else None,
            
        }
    elif order.source == OrderSourceEnum.HOURLY_RENTAL and hourly_rental:
        print("checking hours ..")
        source_data = {
            "id": hourly_rental.id,
            "package_hours": hourly_rental.package_hours,
            "cost_per_hour": hourly_rental.cost_per_hour,
            "extra_cost_per_hour": hourly_rental.extra_cost_per_hour,
            "cost_for_addon_km": hourly_rental.cost_for_addon_km,
            "extra_cost_for_addon_km": hourly_rental.extra_cost_for_addon_km,
            "pickup_notes": hourly_rental.pickup_notes,
        }
    else:
        source_data = None

    return {**base_data, "source_data": source_data}


def map_to_combined_schema_pending_orders(order, new_order=None, hourly_rental=None, db : Session = None):
    # BaseOrderSchema fields
    order_assignment = db.query(OrderAssignment).filter(OrderAssignment.order_id == order.id).first()
    order_accept_status= (
            order_assignment is not None and 
            order_assignment.assignment_status in (AssignmentStatusEnum.PENDING, AssignmentStatusEnum.ASSIGNED)
        )
    base_data = {
        "id": order.id,
        "source": order.source.value,  # enum as string
        "source_order_id": order.source_order_id,
        "vendor_id": order.vendor_id,  # UUID, ensure correct type
        "trip_type": order.trip_type.value,
        "car_type": order.car_type.value,
        "pickup_drop_location": order.pickup_drop_location,
        "start_date_time": order.start_date_time,
        "customer_name": order.customer_name,
        "customer_number": order.customer_number,
        "trip_status": order.trip_status,
        "pick_near_city": order.pick_near_city,
        "trip_distance": order.trip_distance,
        "trip_time": order.trip_time,
        "estimated_price": order.estimated_price,
        "vendor_price": order.vendor_price,
        "platform_fees_percent": order.platform_fees_percent,
        "closed_vendor_price": order.closed_vendor_price,
        "closed_driver_price": order.closed_driver_price,
        "commision_amount": order.commision_amount,
        "created_at": order.created_at,
        "cost_per_km" : new_order.cost_per_km if new_order else None,
        "venodr_profit" : order.vendor_profit if order else None,
        "admin_profit" : order.admin_profit if order else None,
        "order_accept_status": order_accept_status,
        "Driver_assigned": (order_accept_status and order_assignment.driver_id is not None),
        "Car_assigned": (order_accept_status and order_assignment.car_id is not None)
        

    }
    print("Base Data:", base_data)

    # source_data based on source type
    if order.source == OrderSourceEnum.NEW_ORDERS and new_order:
        source_data = {
            "order_id": new_order.order_id,
            "cost_per_km": new_order.cost_per_km,
            "extra_cost_per_km": new_order.extra_cost_per_km,
            "driver_allowance": new_order.driver_allowance,
            "extra_driver_allowance": new_order.extra_driver_allowance,
            "permit_charges": new_order.permit_charges,
            "extra_permit_charges": new_order.extra_permit_charges,
            "hill_charges": new_order.hill_charges,
            "toll_charges": new_order.toll_charges,
            "pickup_notes": new_order.pickup_notes,
            # "cost_per_km" : order.cost_per_km if hasattr(order, 'cost_per_km') else None,
            # "venodr_profit" : order.vendor_profit if order else None,
        }
    elif order.source == OrderSourceEnum.HOURLY_RENTAL and hourly_rental:
        source_data = {
            "id": hourly_rental.id,
            "package_hours": hourly_rental.package_hours,
            "cost_per_hour": hourly_rental.cost_per_hour,
            "extra_cost_per_hour": hourly_rental.extra_cost_per_hour,
            "cost_for_addon_km": hourly_rental.cost_for_addon_km,
            "extra_cost_for_addon_km": hourly_rental.extra_cost_for_addon_km,
            "pickup_notes": hourly_rental.pickup_notes,
        }
    else:
        source_data = None

    return {**base_data, "source_data": source_data}

def get_vendor_orders(db: Session, vendor_id: str):
    query = (
        db.query(Order, NewOrder, HourlyRental)
        .outerjoin(
            NewOrder,
            (Order.source == OrderSourceEnum.NEW_ORDERS) &
            (Order.source_order_id == NewOrder.order_id)
        )
        .outerjoin(
            HourlyRental,
            (Order.source == OrderSourceEnum.HOURLY_RENTAL) &
            (Order.source_order_id == HourlyRental.id)
        )
        .filter(Order.vendor_id == vendor_id)
        .order_by(Order.created_at.desc())
    )
    # print("Constructed Query:")

    results = query.all()

    # map each row to CombinedOrderSchema dict
    combined_orders = [
        map_to_combined_schema(order, new_order, hourly_rental)
        for order, new_order, hourly_rental in results
    ]

    return combined_orders

def get_vendor_pending_orders(db: Session, vendor_id: str):
    query = (
        db.query(Order, NewOrder, HourlyRental)
        .outerjoin(
            NewOrder,
            (Order.source == OrderSourceEnum.NEW_ORDERS) &
            (Order.source_order_id == NewOrder.order_id)
        )
        .outerjoin(
            HourlyRental,
            (Order.source == OrderSourceEnum.HOURLY_RENTAL) &
            (Order.source_order_id == HourlyRental.id)
        )
        .filter(Order.vendor_id == vendor_id)
        .filter(Order.trip_status == 'PENDING')
        .order_by(Order.created_at.desc())
    )

    results = query.all()

    # map each row to CombinedOrderSchema dict
    combined_orders = [
        map_to_combined_schema_pending_orders(order, new_order, hourly_rental,db)
        for order, new_order, hourly_rental in results
    ]

    return combined_orders


def get_max_time_to_assign_by_trip_type(db: Session) -> Dict[str, int]:
    """
    Get the maximum time to assign orders from existing orders for each trip type.
    Returns the maximum time in minutes for oneway, roundtrip, multicity, and hourly rental.
    """
    trip_types = [OrderTypeEnum.ONEWAY, OrderTypeEnum.ROUND_TRIP, OrderTypeEnum.MULTY_CITY, OrderTypeEnum.HOURLY_RENTAL]
    max_times = {}
    
    for trip_type in trip_types:
        # Get orders for this trip type
        orders = db.query(Order).filter(Order.trip_type == trip_type).all()
        
        if not orders:
            # If no orders exist for this trip type, use default 15 minutes
            max_times[trip_type.value] = 15
            continue
            
        # Calculate the time difference between created_at and max_time_to_assign_order
        max_time_minutes = 0
        for order in orders:
            if order.max_time_to_assign_order and order.created_at:
                time_diff = (order.max_time_to_assign_order - order.created_at).total_seconds() / 60
                max_time_minutes = max(max_time_minutes, int(time_diff))
        
        # If no valid time differences found, use default 15 minutes
        if max_time_minutes == 0:
            max_time_minutes = 15
            
        max_times[trip_type.value] = max_time_minutes
    
    return max_times


def get_max_time_for_trip_type(db: Session, trip_type: OrderTypeEnum) -> int:
    """
    Get the maximum time to assign orders for a specific trip type.
    Returns the maximum time in minutes.
    """
    # Get orders for this trip type
    orders = db.query(Order).filter(Order.trip_type == trip_type).all()
    
    if not orders:
        # If no orders exist for this trip type, use default 15 minutes
        return 15
        
    # Calculate the time difference between created_at and max_time_to_assign_order
    max_time_minutes = 0
    for order in orders:
        if order.max_time_to_assign_order and order.created_at:
            time_diff = (order.max_time_to_assign_order - order.created_at).total_seconds() / 60
            max_time_minutes = max(max_time_minutes, int(time_diff))
    
    # If no valid time differences found, use default 15 minutes
    if max_time_minutes == 0:
        max_time_minutes = 15
        
    return max_time_minutes


def close_order(
    db: Session,
    *,
    order_id: int,
    closed_vendor_price: int,
    closed_driver_price: int,
    commision_amount: int,
    driver_id: str,
    start_km: int,
    end_km: int,
    contact_number: str,
    image_file,
    image_folder: str = "order_closures"
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found")

    # Upload image first
    img_url = upload_image_to_gcs(image_file, folder=image_folder)

    # Validate km for non-hourly orders when trip_distance present
    if order.trip_distance is not None:
        distance_delta = int(end_km) - int(start_km)
        if distance_delta < int(order.trip_distance):
            raise ValueError("End KM minus Start KM must be greater than or equal to trip distance")

    # Update order closing fields
    order.closed_vendor_price = int(closed_vendor_price)
    order.closed_driver_price = int(closed_driver_price)
    order.commision_amount = int(commision_amount)

    # Create end record
    end_record = EndRecord(
        order_id=order_id,
        driver_id=driver_id,
        start_km=int(start_km),
        end_km=int(end_km),
        contact_number=str(contact_number),
        img_url=img_url,
    )
    db.add(end_record)
    db.commit()
    db.refresh(order)
    db.refresh(end_record)
    return order, end_record, img_url


def get_order_by_id(db: Session, order_id: int) -> Order:
    """Get order by ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def get_new_order_by_id(db: Session, order_id: int) -> NewOrder:
    """Get new order by ID"""
    return db.query(NewOrder).filter(NewOrder.order_id == order_id).first()


def get_hourly_rental_by_id(db: Session, rental_id: int) -> HourlyRental:
    """Get hourly rental by ID"""
    return db.query(HourlyRental).filter(HourlyRental.id == rental_id).first()


def recreate_order(db: Session, order_id: int, current_vendor_id: str, max_time_to_assign_order: int = 15) -> Dict[str, any]:
    """
    Recreate an order based on an existing order ID.
    Validates that the order belongs to the current vendor and is auto_cancelled.
    """
    # Get the master order
    master_order = get_order_by_id(db, order_id)
    if not master_order:
        raise ValueError("Order not found")
    
    # Validate vendor ownership
    if str(master_order.vendor_id) != str(current_vendor_id):
        raise ValueError("Order does not belong to the current vendor")
    
    # Validate that order is auto_cancelled
    if master_order.cancelled_by != "AUTO_CANCELLED":
        raise ValueError("Order can only be recreated if it was auto_cancelled")
    
    # Get source order data based on source type
    if master_order.source == OrderSourceEnum.NEW_ORDERS:
        source_order = get_new_order_by_id(db, master_order.source_order_id)
        if not source_order:
            raise ValueError("Source new order not found")
        
        # Create new order with same data
        new_order = NewOrder(
            vendor_id=source_order.vendor_id,
            trip_type=source_order.trip_type,
            car_type=source_order.car_type,
            pickup_drop_location=source_order.pickup_drop_location,
            start_date_time=source_order.start_date_time,
            customer_name=source_order.customer_name,
            customer_number=source_order.customer_number,
            cost_per_km=source_order.cost_per_km,
            extra_cost_per_km=source_order.extra_cost_per_km,
            driver_allowance=source_order.driver_allowance,
            extra_driver_allowance=source_order.extra_driver_allowance,
            permit_charges=source_order.permit_charges,
            extra_permit_charges=source_order.extra_permit_charges,
            hill_charges=source_order.hill_charges,
            toll_charges=source_order.toll_charges,
            pickup_notes=source_order.pickup_notes,
            trip_status="PENDING",
            pick_near_city=source_order.pick_near_city,
            trip_distance=source_order.trip_distance,
            trip_time=source_order.trip_time,
            platform_fees_percent=source_order.platform_fees_percent,
            estimated_price=source_order.estimated_price,
            vendor_price=source_order.vendor_price,
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        # Create new master order
        new_master_order = create_master_from_new_order(
            db, 
            new_order, 
            max_time_to_assign_order=max_time_to_assign_order, 
            toll_charge_update=master_order.toll_charge_update
        )
        
        return {
            "order_id": new_master_order.id,
            "trip_status": new_master_order.trip_status,
            "pick_near_city": new_master_order.pick_near_city,
            "trip_type": new_master_order.trip_type.value,
            "vendor_price": new_master_order.vendor_price,
            "estimated_price": new_master_order.estimated_price,
            "trip_time": new_master_order.trip_time,
            "source": "NEW_ORDERS"
        }
        
    elif master_order.source == OrderSourceEnum.HOURLY_RENTAL:
        source_order = get_hourly_rental_by_id(db, master_order.source_order_id)
        if not source_order:
            raise ValueError("Source hourly rental not found")
        
        # Create new hourly rental with same data
        new_hourly_order = HourlyRental(
            vendor_id=source_order.vendor_id,
            trip_type=source_order.trip_type,
            car_type=source_order.car_type,
            pickup_drop_location=source_order.pickup_drop_location,
            start_date_time=source_order.start_date_time,
            customer_name=source_order.customer_name,
            customer_number=source_order.customer_number,
            package_hours=source_order.package_hours,
            cost_per_hour=source_order.cost_per_hour,
            extra_cost_per_hour=source_order.extra_cost_per_hour,
            cost_for_addon_km=source_order.cost_for_addon_km,
            extra_cost_for_addon_km=source_order.extra_cost_for_addon_km,
            pickup_notes=source_order.pickup_notes,
        )
        
        db.add(new_hourly_order)
        db.commit()
        db.refresh(new_hourly_order)
        
        # Create new master order
        new_master_order = create_master_from_hourly(
            db,
            new_hourly_order,
            pick_near_city=master_order.pick_near_city,
            trip_time=str(new_hourly_order.package_hours.get("hours", 0)),
            estimated_price=master_order.estimated_price,
            vendor_price=master_order.vendor_price,
            max_time_to_assign_order=max_time_to_assign_order,
            toll_charge_update=master_order.toll_charge_update,
        )
        
        return {
            "order_id": new_master_order.id,
            "order_status": new_master_order.trip_status,
            "picup_near_city": new_master_order.pick_near_city,
            "vendor_price": new_master_order.vendor_price,
            "estimated_price": new_master_order.estimated_price,
            "trip_type": new_master_order.trip_type.value,
            "trip_time": new_master_order.trip_time,
            "source": "HOURLY_RENTAL"
        }
    
    else:
        raise ValueError("Unknown order source type")


