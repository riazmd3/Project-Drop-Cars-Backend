from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate,NotificationUpdate, NotificationPermissionUpdate
import httpx
from app.models.orders import Order
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.models.car_details import CarDetails
from app.models.car_driver import CarDriver
from app.models.order_assignments import OrderAssignment

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
    return db.query(Notification).filter(Notification.permission1 == True,Notification.user == "vehicle_owner").all()

async def send_push_notifications_vehicle_owner(db: Session, title: str, message: str):
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
    
def get_users_vendor_permission_2(db: Session, user_id: str):
    return db.query(Notification).filter(
        Notification.permission2 == True,
        Notification.user == "vendor",
        Notification.sub == user_id  # assuming this is a string
    ).all()

async def send_push_notification_to_vendor(db: Session, order_id: str, title: str, message: str, vehicle_owner_id : str):
    order = db.query(Order).filter(Order.id == order_id).first()
    vehicle_owner = db.query(VehicleOwnerDetails).filter(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id).first()
    if not order:
        return {"status": "Order not found"}

    user_id = str(order.vendor_id)  # convert UUID to string if necessary
    notifications = get_users_vendor_permission_2(db, user_id)

    # Extract tokens
    tokens = [n.token for n in notifications if n.token]

    if not tokens:
        return {"status": f"No Expo push tokens found for vendor with ID: {user_id}"}

    # Prepare payloads (one payload per token)
    payloads = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": message + str(" "+vehicle_owner.full_name)
        }
        for token in tokens
    ]

    # Send notification to Expo
    async with httpx.AsyncClient() as client:
        response = await client.post(EXPO_PUSH_URL, json=payloads)

    return {
        "status": "Notification(s) sent",
        "tokens": tokens,
        "expo_response": response.json()
    }
    
# async def send_push_notification_to_vendor_driver(db: Session, order_id: str, vehicle_owner_id : str , driver_id : str, car_id :str):
#     order = db.query(Order).filter(Order.id == order_id).first()
#     vehicle_owner = db.query(VehicleOwnerDetails).filter(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id).first()
#     car_info = db.query(CarDetails).filter(CarDetails.id == car_id).first()
#     car_driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()
#     if not order:
#         return {"status": "Order not found"}

#     user_id = str(order.vendor_id)  # convert UUID to string if necessary
#     notifications = get_users_vendor_permission_2(db, user_id)

#     # Extract tokens
#     tokens = [n.token for n in notifications if n.token]

#     if not tokens:
#         return {"status": f"No Expo push tokens found for vendor with ID: {user_id}"}

#     # Prepare payloads (one payload per token)
#     payloads = [
#         {
#             "to": token,
#             "sound": "default",
#             "title": "title",
#             "body": "message" + str(vehicle_owner.full_name)
#         }
#         for token in tokens
#     ]

#     # Send notification to Expo
#     async with httpx.AsyncClient() as client:
#         response = await client.post(EXPO_PUSH_URL, json=payloads)

#     return {
#         "status": "Notification(s) sent",
#         "tokens": tokens,
#         "expo_response": response.json()
#     }

async def send_push_notification_to_vendor_driver(
    db: Session,
    order_id: str,
    vehicle_owner_id: str,
    driver_id: str,
    car_id: str
):
    order = db.query(Order).filter(Order.id == order_id).first()
    vehicle_owner = db.query(VehicleOwnerDetails).filter(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id).first()
    car = db.query(CarDetails).filter(CarDetails.id == car_id).first()
    driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()

    if not order:
        return {"status": "Order not found"}

    vendor_id = str(order.vendor_id)

    # Fetch vendor tokens
    vendor_notifications = db.query(Notification).filter(Notification.user == "vendor", Notification.sub == vendor_id).all()
    vendor_tokens = [n.token for n in vendor_notifications if n.token]

    # Fetch driver tokens (if needed)
    driver_tokens = []
    if driver:
        driver_notifications = db.query(Notification).filter(Notification.user == "driver", Notification.sub == str(driver_id)).all()
        driver_tokens = [n.token for n in driver_notifications if n.token]

    payloads = []

    # Notify vendor about car update
    if car and vendor_tokens:
        for token in vendor_tokens:
            payloads.append({
                "to": token,
                "sound": "default",
                "title": f"Order ID: {order_id} -> Car Updated",
                "body": f"'{car.car_name}' has been Assigned for this order by {vehicle_owner.full_name}."
            })

    # Notify vendor about driver update
    if driver and vendor_tokens:
        for token in vendor_tokens:
            payloads.append({
                "to": token,
                "sound": "default",
                "title": f"Order ID: {order_id} -> Driver Updated",
                "body": f"Driver '{driver.full_name}' has been Assigned for this order by {vehicle_owner.full_name}."
            })

    # Notify driver about update
    if driver and driver_tokens:
        for token in driver_tokens:
            payloads.append({
                "to": token,
                "sound": "default",
                "title": "Your Profile Updated",
                "body": "Your driver profile or assignment details have been updated."
            })

    # Send all collected payloads
    if payloads:
        async with httpx.AsyncClient() as client:
            response = await client.post(EXPO_PUSH_URL, json=payloads)
        return {
            "status": "Notification(s) sent",
            "vendor_tokens": vendor_tokens,
            "driver_tokens": driver_tokens,
            "expo_response": response.json()
        }
    else:
        return {"status": "No valid Expo tokens found for vendor or driver"}
    
async def send_trip_status_notification_to_vendor_and_vehicle_owner(
    db: Session,
    order_id: int,
    status: str  # 'started' or 'ended'
):
    if status not in ["started", "ended"]:
        return {"status": "Invalid status. Must be 'started' or 'ended'"}

    # Fetch the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return {"status": "Order not found"}

    # Get the active assignment for this order
    assignment = db.query(OrderAssignment).filter(
        OrderAssignment.order_id == order_id,
        OrderAssignment.assignment_status.in_(["ASSIGNED", "DRIVING", "COMPLETED"])  # Allow active/ended statuses
    ).first()

    if not assignment:
        return {"status": "No active assignment found for this order"}

    vendor_id = str(order.vendor_id)
    vehicle_owner_id = str(assignment.vehicle_owner_id)

    # Create the message
    if status == "started":
        title = f"Order ID: {order_id} Trip Started"
        body = f"The trip for customer '{order.customer_name}' has started."
    else:
        title = f"Order ID: {order_id} Trip Ended"
        body = f"The trip for customer '{order.customer_name}' has Completed."

    payloads = []

    # Fetch vendor tokens
    vendor_notifications = db.query(Notification).filter(
        Notification.user == "vendor",
        Notification.sub == vendor_id
    ).all()
    vendor_tokens = [n.token for n in vendor_notifications if n.token]

    # Fetch vehicle owner tokens
    owner_notifications = db.query(Notification).filter(
        Notification.user == "vehicle_owner",
        Notification.sub == vehicle_owner_id
    ).all()
    owner_tokens = [n.token for n in owner_notifications if n.token]

    # Prepare payloads
    for token in vendor_tokens:
        payloads.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body
        })

    for token in owner_tokens:
        payloads.append({
            "to": token,
            "sound": "default",
            "title": title,
            "body": body
        })

    if not payloads:
        return {"status": "No push tokens found for vendor or vehicle owner"}

    # Send notifications
    async with httpx.AsyncClient() as client:
        response = await client.post(EXPO_PUSH_URL, json=payloads)

    return {
        "status": f"Trip {status} notifications sent",
        "vendor_tokens": vendor_tokens,
        "vehicle_owner_tokens": owner_tokens,
        "expo_response": response.json()
    }

async def notify_vendor_auto_cancelled_order(
    db: Session,
    vendor_id: str,
    order_id: int,
    penalty_amount: int
):
    # Fetch vendor notification tokens
    notifications = db.query(Notification).filter(
        Notification.user == "vendor",
        Notification.sub == str(vendor_id)
    ).all()

    tokens = [n.token for n in notifications if n.token]

    if not tokens:
        return {"status": f"No Expo tokens found for vendor {vendor_id}"}

    # Build notification content
    title = "Order Auto-Cancelled"
    body = f"Order #{order_id} was auto-cancelled. A penalty of ₹{penalty_amount} has been received."

    payloads = [
        {
            "to": token,
            "sound": "default",
            "title": title,
            "body": body
        }
        for token in tokens
    ]

    # Send push notification
    async with httpx.AsyncClient() as client:
        response = await client.post(EXPO_PUSH_URL, json=payloads)

    return {
        "status": "Auto-cancel notification sent",
        "tokens": tokens,
        "expo_response": response.json()
    }