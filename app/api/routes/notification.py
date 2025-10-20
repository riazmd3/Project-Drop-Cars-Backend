from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.notification import NotificationResponse, NotificationCreate, NotificationPermissionUpdate
from app.database.session import get_db
from app.core.security import get_current_user_sub
from app.crud.notification import get_notification,update_notification, create_notification, update_permissions_only

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/", response_model=NotificationResponse)
def get_user_notification(
    sub: str = Depends(get_current_user_sub),
    db: Session = Depends(get_db)
):
    notif = get_notification(db, sub)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notif

@router.post("/", response_model=NotificationResponse)
def toggle_or_create_notification(
    data: NotificationCreate,
    sub: str = Depends(get_current_user_sub),
    db: Session = Depends(get_db)
):
    existing = get_notification(db, sub)
    if existing:
        updated = update_notification(db, sub, data)
        return updated
    else:
        created = create_notification(db, sub, data)
        return created
    
@router.patch("/permissions", response_model=NotificationResponse)
def update_permissions(
    data: NotificationPermissionUpdate,
    sub: str = Depends(get_current_user_sub),
    db: Session = Depends(get_db)
):
    notif = get_notification(db, sub)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification record not found")

    updated = update_permissions_only(db, sub, data)
    return updated