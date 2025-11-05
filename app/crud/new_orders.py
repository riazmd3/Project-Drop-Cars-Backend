from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any, List, Tuple

from app.models.new_orders import NewOrder, OrderTypeEnum, CarTypeEnum
from app.utils.maps import get_distance_km_between_locations
from app.crud.orders import create_master_from_new_order


def _origin_and_destination_from_index_map(index_map: Dict[str, str]) -> (str, str):
    # keys are numeric-like strings: '0', '1', ...
    sorted_keys = sorted(index_map.keys(), key=lambda k: int(k))
    origin_key = sorted_keys[0]
    destination_key = sorted_keys[-1]
    return index_map[origin_key], index_map[destination_key]


def calculate_oneway_fare(pickup_drop_location: Dict[str, str], cost_per_km: int, driver_allowance: int, extra_driver_allowance: int, permit_charges: int,extra_permit_charges: int, hill_charges: int, toll_charges: int, extra_cost_per_km:int) -> Dict[str, Any]:
    origin, destination = _origin_and_destination_from_index_map(pickup_drop_location)
    total_km,duration_text = get_distance_km_between_locations(origin, destination)
    base_km_amount = int(round(total_km * cost_per_km))
    extra_base_km_amount = int(round(total_km * extra_cost_per_km))
    

    total_amount = base_km_amount + extra_base_km_amount \
        + int(driver_allowance) \
        + int(extra_driver_allowance) \
        + int(permit_charges) \
        + int(extra_permit_charges) \
        + int(hill_charges) \
        + int(toll_charges)

    return {
        "total_km": total_km,
        "trip_time": duration_text,
        "base_km_amount": base_km_amount,
        "driver_allowance": int(driver_allowance),
        "extra_driver_allowance": int(extra_driver_allowance),
        "permit_charges": int(permit_charges),
        "extra_permit_charges": int(extra_permit_charges),
        "hill_charges": int(hill_charges),
        "toll_charges": int(toll_charges),
        "total_amount": int(total_amount),
        "Commission_percent": 10,
    }


def _sorted_location_keys(index_map: Dict[str, str]) -> list:
    return sorted(index_map.keys(), key=lambda k: int(k))


def _sum_multisegment_distance_and_duration(index_map: Dict[str, str]) -> (float, str):
    keys = _sorted_location_keys(index_map)
    if len(keys) < 2:
        return 0.0, "0 min"
    total_km_sum = 0.0
    duration_parts: List[str] = []
    for i in range(len(keys) - 1):
        origin = index_map[keys[i]]
        destination = index_map[keys[i + 1]]
        segment_km, segment_duration = get_distance_km_between_locations(origin, destination)
        total_km_sum += float(segment_km)
        duration_parts.append(segment_duration)
    # Join durations; this is indicative for users and avoids complex parsing
    duration_text = " + ".join(duration_parts)
    return round(total_km_sum), duration_text


def calculate_multisegment_fare(pickup_drop_location: Dict[str, str], cost_per_km: int, driver_allowance: int, extra_driver_allowance: int, permit_charges: int, extra_permit_charges: int, hill_charges: int, toll_charges: int, extra_cost_per_km:int) -> Dict[str, Any]:
    total_km, duration_text = _sum_multisegment_distance_and_duration(pickup_drop_location)
    base_km_amount = int(round(total_km * cost_per_km))
    extra_base_km_amount = int(round(total_km * extra_cost_per_km))

    total_amount = base_km_amount + extra_base_km_amount\
        + int(driver_allowance) \
        + int(extra_driver_allowance) \
        + int(permit_charges) \
        + int(extra_permit_charges) \
        + int(hill_charges) \
        + int(toll_charges)

    return {
        "total_km": total_km,
        "trip_time": duration_text,
        "base_km_amount": base_km_amount,
        "driver_allowance": int(driver_allowance),
        "extra_driver_allowance": int(extra_driver_allowance),
        "permit_charges": int(permit_charges),
        "extra_permit_charges": int(extra_permit_charges),
        "hill_charges": int(hill_charges),
        "toll_charges": int(toll_charges),
        "total_amount": int(total_amount),
        "Commission_percent": 10,
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
    extra_permit_charges: int,
    hill_charges: int,
    toll_charges: int,
    pickup_notes: str,
    trip_distance = int,
    trip_time = str,
    platform_fees_percent = int,
    pick_near_city: list,
    max_time_to_assign_order: int = 15,
    toll_charge_update: bool = False,
    night_charges: int | None = None,
) -> Tuple[NewOrder, int]:
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
        extra_permit_charges=extra_permit_charges,
        hill_charges=hill_charges,
        toll_charges=toll_charges,
        pickup_notes=pickup_notes,
        trip_distance = trip_distance,
        trip_time = trip_time,
        platform_fees_percent = 10,
        trip_status="PENDING",
        estimated_price = (cost_per_km * trip_distance) + driver_allowance + hill_charges + permit_charges + toll_charges,
        vendor_price = ((cost_per_km + extra_cost_per_km) * trip_distance) + (driver_allowance + extra_driver_allowance) + (permit_charges + extra_permit_charges) + hill_charges + toll_charges,
        pick_near_city=pick_near_city,
    )
    # print(cost_per_km,trip_distance,driver_allowance,hill_charges,permit_charges,toll_charges)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    # Also create/refresh master order row
    master_order = create_master_from_new_order(db, new_order, max_time_to_assign_order, toll_charge_update, night_charges=night_charges)
    return new_order, master_order.id


def get_pending_all_city_orders(db: Session) -> List[NewOrder]:
    return db.query(NewOrder).filter(
        NewOrder.trip_status == "PENDING",
        NewOrder.pick_near_city == "ALL"
    ).all()
    
def get_orders_by_vendor_id(db: Session, vendor_id: UUID) -> List[NewOrder]:
    return db.query(NewOrder).filter(NewOrder.vendor_id == vendor_id).order_by(NewOrder.created_at.desc()).all()
