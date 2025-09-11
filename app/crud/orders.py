from sqlalchemy.orm import Session
from typing import List

from app.models.orders import Order, OrderSourceEnum
from app.models.new_orders import NewOrder
from app.models.hourly_rental import HourlyRental


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


def create_master_from_hourly(db: Session, hourly: HourlyRental) -> Order:
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
    )
    db.add(master)
    db.commit()
    db.refresh(master)
    return master


def get_all_orders(db: Session) -> List[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).all()


def get_vendor_orders(db: Session, vendor_id: str) -> List[Order]:
    return db.query(Order).filter(Order.vendor_id == vendor_id).order_by(Order.created_at.desc()).all()


