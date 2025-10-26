from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.vehicle_owner import VehicleOwnerCredentials
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.schemas.vehicle_owner import VehicleOwnerBase, VehicleOwnerForm, UserLogin
from app.core.security import get_password_hash, verify_password
from typing import Optional
from uuid import UUID

def create_user(db: Session, user_in: VehicleOwnerForm) -> VehicleOwnerCredentials:
    # Check for duplicate primary number in main vehicle_owner table
    existing_user = db.query(VehicleOwnerCredentials).filter(
        VehicleOwnerCredentials.primary_number == user_in.primary_number
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"Mobile number {user_in.primary_number} is already registered. Please use a different number."
        )

    # Check for duplicate secondary number (only if provided)
    if user_in.secondary_number:
        existing_secondary = db.query(VehicleOwnerDetails).filter(
            VehicleOwnerDetails.secondary_number == user_in.secondary_number
        ).first()
        if existing_secondary:
            raise HTTPException(
                status_code=400,
                detail=f"Secondary mobile number {user_in.secondary_number} is already registered. Please use a different number."
            )



    # Check for duplicate Aadhar number
    existing_aadhar = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.aadhar_number == user_in.aadhar_number
    ).first()
    if existing_aadhar:
        raise HTTPException(
            status_code=400,
            detail=f"Aadhar number {user_in.aadhar_number} is already registered. Please use a different number."
        )

    # Step 1: Hash password
    hashed_password = get_password_hash(user_in.password)

    # Step 2: Create credentials object
    credentials = VehicleOwnerCredentials(
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
        full_name=user_in.full_name,
        primary_number=user_in.primary_number,
        secondary_number=user_in.secondary_number,
        wallet_balance=0,
        aadhar_number=user_in.aadhar_number,
        aadhar_front_img=None,  # Will be updated after GCS upload
        address=user_in.address,
        city=user_in.city,
        pincode=user_in.pincode
    )

    db.add(details)
    db.commit()
    db.refresh(credentials)

    return credentials


def update_aadhar_image(db: Session, vehicle_owner_id: UUID, aadhar_img_url: str) -> VehicleOwnerDetails:
    """Update the aadhar_front_img URL for an existing vehicle owner"""
    from app.models.common_enums import DocumentStatusEnum
    
    details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()
    
    if not details:
        raise HTTPException(
            status_code=404, 
            detail=f"Vehicle owner details not found for ID: {vehicle_owner_id}"
        )
    
    details.aadhar_front_img = aadhar_img_url
    details.aadhar_status = DocumentStatusEnum.PENDING  # Set status to Pending when image is updated
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

def get_vehicle_owner_by_id(db: Session, vehicle_owner_id: str) -> Optional[VehicleOwnerCredentials]:
    """Get vehicle owner by ID"""
    try:
        owner_uuid = UUID(vehicle_owner_id)
        return db.query(VehicleOwnerCredentials).filter(VehicleOwnerCredentials.id == owner_uuid).first()
    except ValueError:
        return None


def get_user_by_mobile(db: Session, mobile_number: str) -> Optional[VehicleOwnerCredentials]:
    return db.query(VehicleOwnerCredentials).filter(VehicleOwnerCredentials.primary_number == mobile_number).first()


def authenticate_user(db: Session, login_data: UserLogin) -> Optional[VehicleOwnerCredentials]:
    user = get_user_by_mobile(db, login_data.mobile_number)
    if not user or not verify_password(login_data.password, user.hashed_password):
        return None
    return user


def get_vehicle_owner_counts(db: Session, vehicle_owner_id: UUID):
    """Get counts of car_driver and car_details records for a vehicle owner"""
    from app.models.car_driver import CarDriver
    from app.models.car_details import CarDetails
    
    # Count car_driver records with matching vehicle_owner_id
    car_driver_count = db.query(CarDriver).filter(
        CarDriver.vehicle_owner_id == vehicle_owner_id
    ).count()
    
    # Count car_details records with matching vehicle_owner_id
    car_details_count = db.query(CarDetails).filter(
        CarDetails.vehicle_owner_id == vehicle_owner_id
    ).count()
    
    return {
        "car_driver_count": car_driver_count,
        "car_details_count": car_details_count
    }


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
def get_vehicle_owner_by_id(db: Session, vehicle_owner_id: UUID):
    return db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()