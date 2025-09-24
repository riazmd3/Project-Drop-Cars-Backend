from sqlalchemy.orm import Session
from typing import List

from app.models.orders import Order, OrderSourceEnum
from app.models.end_records import EndRecord
from app.utils.gcs import upload_image_to_gcs
from app.models.new_orders import NewOrder
from app.models.hourly_rental import HourlyRental
from sqlalchemy.sql import or_, and_


def create_master_from_new_order(db: Session, new_order: NewOrder) -> Order:
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
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    return master


def create_master_from_hourly(db: Session, hourly: HourlyRental, *, pick_near_city: str, trip_time : int, estimated_price: int, vendor_price:int) -> Order:
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
        estimated_price = estimated_price,
        vendor_price = vendor_price+estimated_price,
        platform_fees_percent = 10
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    return master


def get_all_orders(db: Session) -> List[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).all()


# def get_vendor_orders(db: Session, vendor_id: str) -> List[Order]:
#     print("Vendor ID in CRUD:", vendor_id)
#     return db.query(Order).filter(Order.vendor_id == vendor_id).order_by(Order.created_at.desc()).all()


def map_to_combined_schema(order, new_order=None, hourly_rental=None):
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
    }

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
        }
    elif order.source == OrderSourceEnum.HOURLY_RENTAL and hourly_rental:
        source_data = {
            "id": hourly_rental.id,
            "package_hours": hourly_rental.package_hours,
            "cost_per_pack": hourly_rental.cost_per_pack,
            "extra_cost_per_pack": hourly_rental.extra_cost_per_pack,
            "additional_cost_per_hour": hourly_rental.additional_cost_per_hour,
            "extra_additional_cost_per_hour": hourly_rental.extra_additional_cost_per_hour,
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

    results = query.all()

    # map each row to CombinedOrderSchema dict
    combined_orders = [
        map_to_combined_schema(order, new_order, hourly_rental)
        for order, new_order, hourly_rental in results
    ]

    return combined_orders



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


