from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict

from app.database.session import get_db
from app.core.security import get_current_vendor
from app.schemas.new_orders import (
    OnewayQuoteRequest,
    OnewayQuoteResponse,
    OnewayConfirmRequest,
    OnewayConfirmResponse,
    RoundTripQuoteRequest,
    RoundTripConfirmRequest,
    MulticityQuoteRequest,
    MulticityConfirmRequest,
    FareBreakdown,NewOrderResponse
)
from app.crud.new_orders import calculate_oneway_fare, calculate_multisegment_fare, create_oneway_order, get_pending_all_city_orders, get_orders_by_vendor_id
from app.crud.order_assignments import get_vendor_orders_with_assignments
from app.schemas.order_assignments import OrderAssignmentWithOrderDetails
from app.models.new_orders import OrderTypeEnum, CarTypeEnum
from app.schemas.baseorder import BaseOrderSchema
from app.crud.orders import get_vendor_orders


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
            payload.extra_cost_per_km,
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
            payload.extra_cost_per_km,
        )
        
        # Persist order
        new_order, master_order_id = create_oneway_order(
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
            max_time_to_assign_order=payload.max_time_to_assign_order,
        )
        print(fare)

        return OnewayConfirmResponse(
            order_id=master_order_id,  # Return master order ID instead of new_order.order_id
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


@router.post("/roundtrip/quote", response_model=OnewayQuoteResponse)
async def roundtrip_quote(payload: RoundTripQuoteRequest):
    try:
        fare = calculate_multisegment_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
            payload.extra_cost_per_km,
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


@router.post("/roundtrip/confirm", response_model=OnewayConfirmResponse, status_code=status.HTTP_201_CREATED)
async def roundtrip_confirm(
    payload: RoundTripConfirmRequest,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    try:
        vendor_id = current_vendor.id
        pick_near_city = payload.near_city if payload.send_to == "NEAR_CITY" else "ALL"
        if payload.send_to == "NEAR_CITY" and not payload.near_city:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="near_city is required when send_to is NEAR_CITY",
            )

        fare = calculate_multisegment_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
            payload.extra_cost_per_km
        )

        new_order, master_order_id = create_oneway_order(
            db,
            vendor_id=vendor_id,
            trip_type=OrderTypeEnum.ROUND_TRIP,
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
            max_time_to_assign_order=payload.max_time_to_assign_order,
        )

        return OnewayConfirmResponse(
            order_id=master_order_id,  # Return master order ID instead of new_order.order_id
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


@router.post("/multicity/quote", response_model=OnewayQuoteResponse)
async def multicity_quote(payload: MulticityQuoteRequest):
    try:
        fare = calculate_multisegment_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
            payload.extra_cost_per_km
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


@router.post("/multicity/confirm", response_model=OnewayConfirmResponse, status_code=status.HTTP_201_CREATED)
async def multicity_confirm(
    payload: MulticityConfirmRequest,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    try:
        vendor_id = current_vendor.id
        pick_near_city = payload.near_city if payload.send_to == "NEAR_CITY" else "ALL"
        if payload.send_to == "NEAR_CITY" and not payload.near_city:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="near_city is required when send_to is NEAR_CITY",
            )

        fare = calculate_multisegment_fare(
            payload.pickup_drop_location,
            payload.cost_per_km,
            payload.driver_allowance,
            payload.extra_driver_allowance,
            payload.permit_charges,
            payload.extra_permit_charges,
            payload.hill_charges,
            payload.toll_charges,
            payload.extra_cost_per_km,
        )

        new_order, master_order_id = create_oneway_order(
            db,
            vendor_id=vendor_id,
            trip_type=OrderTypeEnum.MULTY_CITY,
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
            max_time_to_assign_order=payload.max_time_to_assign_order,
        )

        return OnewayConfirmResponse(
            order_id=master_order_id,  # Return master order ID instead of new_order.order_id
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

@router.get("/pending-all", response_model=List[NewOrderResponse])
def get_pending_all_orders(db: Session = Depends(get_db)):
    return get_pending_all_city_orders(db)

@router.get("/vendor", response_model=List[BaseOrderSchema])
def get_vendor_orderss(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor)
):
    return get_vendor_orders(db, current_vendor.id)


@router.get("/vendor/with-assignments", response_model=List[OrderAssignmentWithOrderDetails])
def get_vendor_orders_with_assignmentss(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor)
):
    """Get all orders for the authenticated vendor with their latest assignment details"""
    print("current_vendor", current_vendor.id)
    return get_vendor_orders_with_assignments(db, str(current_vendor.id))