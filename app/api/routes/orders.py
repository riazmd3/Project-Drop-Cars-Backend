from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_vendor
from app.schemas.new_orders import UnifiedOrder, CloseOrderResponse
from app.crud.orders import get_all_orders, get_vendor_orders, close_order


router = APIRouter()


@router.get("/all", response_model=List[UnifiedOrder])
def list_all_orders(db: Session = Depends(get_db)):
    return get_all_orders(db)


@router.get("/vendor", response_model=List[UnifiedOrder])
def list_vendor_orders(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    return get_vendor_orders(db, current_vendor.id)


@router.post("/{order_id}/close", response_model=CloseOrderResponse)
async def close_order_endpoint(
    order_id: int,
    closed_vendor_price: int = Form(...),
    closed_driver_price: int = Form(...),
    commision_amount: int = Form(...),
    start_km: int = Form(...),
    end_km: int = Form(...),
    contact_number: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    try:
        order, end_record, img_url = close_order(
            db,
            order_id=order_id,
            closed_vendor_price=closed_vendor_price,
            closed_driver_price=closed_driver_price,
            commision_amount=commision_amount,
            driver_id=current_vendor.id,  # if driver closes, replace with driver auth in future
            start_km=start_km,
            end_km=end_km,
            contact_number=contact_number,
            image_file=image,
        )
        return CloseOrderResponse(order_id=order.id, end_record_id=end_record.id, img_url=img_url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


