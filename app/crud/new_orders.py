from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.models.new_orders import NewOrder, OrderTypeEnum, CarTypeEnum
from app.utils.maps import get_distance_km_between_locations


def _origin_and_destination_from_index_map(index_map: Dict[str, str]) -> (str, str):
    # keys are numeric-like strings: '0', '1', ...
    sorted_keys = sorted(index_map.keys(), key=lambda k: int(k))
    origin_key = sorted_keys[0]
    destination_key = sorted_keys[-1]
    return index_map[origin_key], index_map[destination_key]


def calculate_oneway_fare(pickup_drop_location: Dict[str, str], cost_per_km: int, driver_allowance: int, extra_driver_allowance: int, permit_charges: int, hill_charges: int, toll_charges: int) -> Dict[str, Any]:
    origin, destination = _origin_and_destination_from_index_map(pickup_drop_location)
    total_km = get_distance_km_between_locations(origin, destination)
    base_km_amount = int(round(total_km * cost_per_km))

    total_amount = base_km_amount \
        + int(driver_allowance) \
        + int(extra_driver_allowance) \
        + int(permit_charges) \
        + int(hill_charges) \
        + int(toll_charges)

    return {
        "total_km": total_km,
        "base_km_amount": base_km_amount,
        "driver_allowance": int(driver_allowance),
        "extra_driver_allowance": int(extra_driver_allowance),
        "permit_charges": int(permit_charges),
        "hill_charges": int(hill_charges),
        "toll_charges": int(toll_charges),
        "total_amount": int(total_amount),
    }


def create_oneway_order(
    db: Session,
    *,
    vendor_id: UUID,
    trip_type: OrderTypeEnum,
    car_type: CarTypeEnum,
    pickup_drop_location,
    start_date_time,
    customer_name: str,
    customer_number: str,
    cost_per_km: int,
    extra_cost_per_km: int,
    driver_allowance: int,
    extra_driver_allowance: int,
    permit_charges: int,
    hill_charges: int,
    toll_charges: int,
    pickup_notes: str,
    pick_near_city: str,
) -> NewOrder:
    new_order = NewOrder(
        vendor_id=vendor_id,
        trip_type=trip_type,
        car_type=car_type,
        pickup_drop_location=pickup_drop_location,
        start_date_time=start_date_time,
        customer_name=customer_name,
        customer_number=customer_number,
        cost_per_km=cost_per_km,
        extra_cost_per_km=extra_cost_per_km,
        driver_allowance=driver_allowance,
        extra_driver_allowance=extra_driver_allowance,
        permit_charges=permit_charges,
        hill_charges=hill_charges,
        toll_charges=toll_charges,
        pickup_notes=pickup_notes,
        trip_status="CONFIRMED",
        pick_near_city=pick_near_city,
    )

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


