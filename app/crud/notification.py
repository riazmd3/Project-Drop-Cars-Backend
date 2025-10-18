from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate,NotificationUpdate, NotificationPermissionUpdate
import httpx

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def get_notification(db: Session, sub: str):
    print("The Sube us ",sub[0])
    return db.query(Notification).filter(Notification.sub == sub[0]).first()

def create_notification(db: Session, sub: str, data: NotificationCreate):
    db_notification = Notification(
        user = sub[1],
        sub=sub[0],
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

def get_users_with_permission1(db: Session):
    return db.query(Notification).filter(Notification.permission1 == True,Notification.user == "vendor").all()

async def send_push_notifications_driver(db: Session, title: str, message: str):
    users = get_users_with_permission1(db)
    tokens = [user.token for user in users if user.token]
    print(tokens)

    if not tokens:
        return {"status": "No tokens found for users with permission1 = True"}

    payloads = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": message
        }
        for token in tokens
    ]

    async with httpx.AsyncClient() as client:
        response = await client.post(EXPO_PUSH_URL, json=payloads)

    return {
        "status": "Notifications sent",
        "tokens": tokens,
        "expo_response": response.json()
    }