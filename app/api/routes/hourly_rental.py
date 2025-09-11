from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.security import get_current_vendor
from app.schemas.new_orders import (
    RentalOrderRequest,
    HourlyQuoteResponse,
    RentalFareBreakdown,
)
from app.crud.hourly_rental import calculate_hourly_fare, create_hourly_order
from app.crud.orders import create_master_from_hourly
from app.models.new_orders import OrderTypeEnum, CarTypeEnum


router = APIRouter()


@router.post("/hourly/quote", response_model=HourlyQuoteResponse)
async def hourly_quote(payload: RentalOrderRequest):
    try:
        fare = calculate_hourly_fare(
            payload.package_hours,
            payload.cost_per_pack,
            payload.extra_cost_per_pack,
            payload.additional_cost_per_hour,
            payload.extra_additional_cost_per_hour,
        )
        return HourlyQuoteResponse(
            fare=RentalFareBreakdown(**fare),
            echo=payload,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate hourly fare: {str(e)}",
        )


@router.post("/hourly/confirm", status_code=status.HTTP_201_CREATED)
async def hourly_confirm(
    payload: RentalOrderRequest,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    try:
        vendor_id = current_vendor.id

        order = create_hourly_order(
            db,
            vendor_id=vendor_id,
            trip_type=OrderTypeEnum.HOURLY_RENTAL,
            car_type=CarTypeEnum(payload.car_type),
            pickup_drop_location=payload.pickup_drop_location,
            start_date_time=payload.start_date_time,
            customer_name=payload.customer_name,
            customer_number=payload.customer_number,
            package_hours=payload.package_hours,
            cost_per_pack=payload.cost_per_pack,
            extra_cost_per_pack=payload.extra_cost_per_pack,
            additional_cost_per_hour=payload.additional_cost_per_hour,
            extra_additional_cost_per_hour=payload.extra_additional_cost_per_hour,
            pickup_notes=payload.pickup_notes or "",
        )

        create_master_from_hourly(db, order, pick_near_city=payload.pick_near_city)

        return {"order_id": order.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to confirm hourly order: {str(e)}",
        )


