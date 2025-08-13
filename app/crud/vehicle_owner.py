from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.vehicle_owner import VehicleOwnerCredentials
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.schemas.vehicle_owner import VehicleOwnerBase, VehicleOwnerForm
from app.core.security import get_password_hash, verify_password
from typing import Optional
from uuid import UUID

def create_user(db: Session, user_in: VehicleOwnerForm) -> VehicleOwnerCredentials:
    # Check for duplicate primary number in main vehicle_owner table
    existing_user = db.query(VehicleOwnerCredentials).filter(
        VehicleOwnerCredentials.primary_number == user_in.primary_number
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # Step 1: Hash password
    hashed_password = get_password_hash(user_in.password)

    # Step 2: Create credentials object
    credentials = VehicleOwnerCredentials(
        organization_id=user_in.organization_id,
        primary_number=user_in.primary_number,
        hashed_password=hashed_password,
        account_status="INACTIVE",
        driver_profile=0,
        car_profile=0,
    )

    db.add(credentials)
    db.flush()  # Important: So we get credentials.id before commit

    # Step 3: Create details object (without aadhar_front_img initially)
    details = VehicleOwnerDetails(
        vehicle_owner_id=credentials.id,
        organization_id=user_in.organization_id,
        full_name=user_in.full_name,
        primary_number=user_in.primary_number,
        secondary_number=user_in.secondary_number,
        wallet_balance=0,
        gpay_number=user_in.gpay_number,
        aadhar_number=user_in.aadhar_number,
        aadhar_front_img=None,  # Will be updated after GCS upload
        adress=user_in.address
    )

    db.add(details)
    db.commit()
    db.refresh(credentials)

    return credentials


def update_aadhar_image(db: Session, vehicle_owner_id: UUID, aadhar_img_url: str) -> VehicleOwnerDetails:
    """Update the aadhar_front_img URL for an existing vehicle owner"""
    details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()
    
    if not details:
        raise HTTPException(status_code=404, detail="Vehicle owner details not found")
    
    details.aadhar_front_img = aadhar_img_url
    db.commit()
    db.refresh(details)
    
    return details

# def create_user(db: Session, user_in: VehicleOwnerBase) -> VehicleOwner:
#     existing_user = db.query(VehicleOwner).filter(VehicleOwner.mobile_number == user_in.mobile_number).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User Number already registered")

#     hashed_password = get_password_hash(user_in.password)
#     db_user = VehicleOwner(
#         full_name=user_in.full_name,
#         mobile_number=user_in.mobile_number,
#         hashed_password=hashed_password,
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def get_user(db: Session, user_id: int) -> Optional[User]:
#     return db.query(User).filter(User.id == user_id).first()

# def get_user_by_mobile(db: Session, mobile_number: str) -> Optional[User]:
#     return db.query(User).filter(User.mobile_number == mobile_number).first()

# def authenticate_user(db: Session, login_data: UserLogin) -> Optional[User]:
#     user = get_user_by_mobile(db, login_data.mobile_number)
#     if not user or not verify_password(login_data.password, user.hashed_password):
#         return None
#     return user

# def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
#     user = get_user(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Update fields except password by default
#     update_data = user_update.dict(exclude_unset=True)
#     if "password" in update_data:
#         update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

#     for key, value in update_data.items():
#         setattr(user, key, value)

#     db.commit()
#     db.refresh(user)
#     return user

# def delete_user(db: Session, user_id: int):
#     user = get_user(db, user_id)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     db.delete(user)
#     db.commit()
