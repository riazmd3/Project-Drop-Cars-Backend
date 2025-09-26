from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_vendor, get_current_driver, get_current_admin
from app.schemas.new_orders import UnifiedOrder, CloseOrderResponse
from app.schemas.order_details import AdminOrderDetailResponse, VendorOrderDetailResponse
from app.crud.orders import get_all_orders, get_vendor_orders, close_order, get_vendor_pending_orders
from app.crud.order_details import get_admin_order_details, get_vendor_order_details


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

@router.get("/pending/vendor", response_model=List[UnifiedOrder])
def list_vendor_orders(
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    return get_vendor_pending_orders(db, current_vendor.id)


@router.get("/admin/{order_id}", response_model=AdminOrderDetailResponse)
async def get_admin_order_details_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    Get full order details for admin with all related data including:
    - Order information
    - Vendor details
    - Assignment history
    - End records
    - Driver and car information
    - Vehicle owner information
    """
    order_details = get_admin_order_details(db, order_id)
    if not order_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order_details


@router.get("/vendor/{order_id}", response_model=VendorOrderDetailResponse)
async def get_vendor_order_details_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
    current_vendor=Depends(get_current_vendor),
):
    """
    Get limited order details for vendor with order-related data but excluding sensitive user information:
    - Order information
    - Assignment history
    - End records
    - Basic driver and car info (names and phone numbers only)
    - No personal details like addresses, IDs, etc.
    """
    order_details = get_vendor_order_details(db, order_id, str(current_vendor.id))
    if not order_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or you don't have permission to view this order"
        )
    
    return order_details


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
    current_driver=Depends(get_current_driver),
):
    try:
        order, end_record, img_url = close_order(
            db,
            order_id=order_id,
            closed_vendor_price=closed_vendor_price,
            closed_driver_price=closed_driver_price,
            commision_amount=commision_amount,
            driver_id=current_driver.id,
            start_km=start_km,
            end_km=end_km,
            contact_number=contact_number,
            image_file=image,
        )
        return CloseOrderResponse(order_id=order.id, end_record_id=end_record.id, img_url=img_url)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


