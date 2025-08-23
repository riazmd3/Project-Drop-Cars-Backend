from pydantic import BaseModel, Field,field_validator
from typing import Any, List, Optional, Union, Literal, Dict
from uuid import UUID
from datetime import datetime
from enum import Enum


class OrderType(str,Enum):
    ONEWAY = "Oneway"


class CarType(str,Enum):
    HATCHBACK = "Hatchback"
    SEDAN = "Sedan"
    NEW_SEDAN = "New Sedan"
    SUV = "SUV"
    INNOVA = "Innova"
    INNOVA_CRYSTA = "Innova Crysta"


class OnewayQuoteRequest(BaseModel):
    vendor_id: UUID
    trip_type: OrderType = Field(default=OrderType.ONEWAY)
    car_type: CarType
    pickup_drop_location: Dict[str, str] = Field(
        description="Object mapping indices to location names, e.g. {\"0\": \"Chennai\", \"1\": \"Bangalore\"}"
    )
    start_date_time: datetime
    customer_name: str
    customer_number: str
    cost_per_km: int
    extra_cost_per_km: int
    driver_allowance: int
    extra_driver_allowance: int
    permit_charges: int
    extra_permit_charges: int
    hill_charges: int
    toll_charges: int
    pickup_notes: Optional[str] = None

    @field_validator("pickup_drop_location")
    def validate_locations(cls, v: Dict[str, str]):
        if not isinstance(v, dict) or len(v.keys()) < 2:
            raise ValueError("pickup_drop_location must be an object with at least two indices: source (0) and destination (last)")
        # Ensure keys are numeric-like
        try:
            sorted([int(k) for k in v.keys()])
        except Exception:
            raise ValueError("pickup_drop_location keys must be numeric strings like '0', '1', ...")
        return v


class OnewayConfirmRequest(OnewayQuoteRequest):
    send_to: Literal["ALL", "NEAR_CITY"] = Field(
        description="Whether to send to all or only near city drivers"
    )
    near_city: Optional[str] = Field(
        default=None, description="City name when send_to is NEAR_CITY"
    )


class FareBreakdown(BaseModel):
    total_km: float
    trip_time: str
    base_km_amount: int
    driver_allowance: int
    extra_driver_allowance: int
    permit_charges: int
    hill_charges: int
    toll_charges: int
    total_amount: int


class OnewayQuoteResponse(BaseModel):
    fare: FareBreakdown
    echo: OnewayQuoteRequest


class OnewayConfirmResponse(BaseModel):
    order_id: int
    trip_status: str
    pick_near_city: str
    fare: FareBreakdown


