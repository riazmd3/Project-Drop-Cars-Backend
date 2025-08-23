from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.session import get_db
from app.core.security import get_current_vendor
from app.schemas.new_orders import (
    OnewayQuoteRequest,
    OnewayQuoteResponse,
    OnewayConfirmRequest,
    OnewayConfirmResponse,
    FareBreakdown,
)
from app.crud.new_orders import calculate_oneway_fare, create_oneway_order
from app.models.new_orders import OrderTypeEnum, CarTypeEnum


router = APIRouter()


@router.post("/oneway/quote", response_model=OnewayQuoteResponse)
async def oneway_quote(payload: OnewayQuoteRequest):
    try:
        fare = calculate_oneway_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
        )
        return OnewayQuoteResponse(
            fare=FareBreakdown(**fare),
            echo=payload,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to calculate fare: {str(e)}",
        )


@router.post("/oneway/confirm", response_model=OnewayConfirmResponse, status_code=status.HTTP_201_CREATED)
async def oneway_confirm(
    payload: OnewayConfirmRequest,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    try:
        # Only vendor from auth can create the order
        vendor_id = current_vendor.id

        # Validate send_to / near_city
        pick_near_city = payload.near_city if payload.send_to == "NEAR_CITY" else "ALL"
        if payload.send_to == "NEAR_CITY" and not payload.near_city:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="near_city is required when send_to is NEAR_CITY",
            )
            
        fare = calculate_oneway_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
        )
        
        # Persist order
        new_order = create_oneway_order(
            db,
            vendor_id=vendor_id,
            trip_type=OrderTypeEnum.ONEWAY,
            car_type=CarTypeEnum(payload.car_type),
            pickup_drop_location=payload.pickup_drop_location,
            start_date_time=payload.start_date_time,
            customer_name=payload.customer_name,
            customer_number=payload.customer_number,
            cost_per_km=payload.cost_per_km,
            extra_cost_per_km=payload.extra_cost_per_km,
            driver_allowance=payload.driver_allowance,
            extra_driver_allowance=payload.extra_driver_allowance,
            permit_charges=payload.permit_charges,
            extra_permit_charges=payload.extra_permit_charges,
            hill_charges=payload.hill_charges,
            toll_charges=payload.toll_charges,
            pickup_notes=payload.pickup_notes or "",
            trip_distance = fare["total_km"],
            trip_time = fare["trip_time"],
            platform_fees_percent = 10,
            pick_near_city=pick_near_city,
        )
        print(fare)

        return OnewayConfirmResponse(
            order_id=new_order.order_id,
            trip_status=new_order.trip_status,
            pick_near_city=new_order.pick_near_city,
            fare=FareBreakdown(**fare),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to confirm order: {str(e)}",
        )


