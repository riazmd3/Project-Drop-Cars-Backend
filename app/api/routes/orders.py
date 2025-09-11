from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.core.security import get_current_vendor
from app.schemas.new_orders import UnifiedOrder
from app.crud.orders import get_all_orders, get_vendor_orders


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


