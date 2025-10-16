from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate,NotificationUpdate, NotificationPermissionUpdate

def get_notification(db: Session, sub: str):
    return db.query(Notification).filter(Notification.sub == sub).first()

def create_notification(db: Session, sub: str, data: NotificationCreate):
    db_notification = Notification(
        sub=sub,
        permission1=data.permission1,
        permission2=data.permission2,
        token=data.token
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def update_notification(db: Session, sub: str, data: NotificationUpdate):
    notification = get_notification(db, sub)
    if notification:
        notification.permission1 = data.permission1
        notification.permission2 = data.permission2
        notification.token = data.token
        db.commit()
        db.refresh(notification)
    return notification

def update_permissions_only(db: Session, sub: str, data: NotificationPermissionUpdate):
    notification = get_notification(db, sub)
    if not notification:
        return None

    if data.permission1 is not None:
        notification.permission1 = data.permission1
    if data.permission2 is not None:
        notification.permission2 = data.permission2

    db.commit()
    db.refresh(notification)
    return notification
