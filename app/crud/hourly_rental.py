from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.models.hourly_rental import HourlyRental
from app.models.new_orders import OrderTypeEnum, CarTypeEnum


def calculate_hourly_fare(
    package_hours: int,
    cost_per_pack: int,
    extra_cost_per_pack: int,
    additional_cost_per_hour: int,
    extra_additional_cost_per_hour: int,
) -> Dict[str, Any]:
    total_hours = float(package_hours)
    estimate_price = int(cost_per_pack)
    vendor_amount = int(cost_per_pack + extra_cost_per_pack)
    return {
        "total_hours": total_hours,
        "vendor_amount": vendor_amount,
        "estimate_price": estimate_price,
    }


def create_hourly_order(
    db: Session,
    *,
    vendor_id: UUID,
    trip_type: OrderTypeEnum,
    car_type: CarTypeEnum,
    pickup_drop_location,
    start_date_time,
    customer_name: str,
    customer_number: str,
    package_hours: int,
    cost_per_pack: int,
    extra_cost_per_pack: int,
    additional_cost_per_hour: int,
    extra_additional_cost_per_hour: int,
    pickup_notes: str,
) -> HourlyRental:
    order = HourlyRental(
        vendor_id=vendor_id,
        trip_type=trip_type,
        car_type=car_type,
        pickup_drop_location=pickup_drop_location,
        start_date_time=start_date_time,
        customer_name=customer_name,
        customer_number=customer_number,
        package_hours=package_hours,
        cost_per_pack=cost_per_pack,
        extra_cost_per_pack=extra_cost_per_pack,
        additional_cost_per_hour=additional_cost_per_hour,
        extra_additional_cost_per_hour=extra_additional_cost_per_hour,
        pickup_notes=pickup_notes,
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


