from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.car_driver import CarDriver, AccountStatusEnum
from app.schemas.car_driver import CarDriverForm
from app.core.security import get_password_hash
from typing import Optional, List
from uuid import UUID

def create_car_driver(db: Session, driver_data: CarDriverForm) -> CarDriver:
    """Create a new car driver record in the database"""
    
    # Check for duplicate primary number
    existing_primary = db.query(CarDriver).filter(
        CarDriver.primary_number == driver_data.primary_number
    ).first()

    if existing_primary:
        raise HTTPException(
            status_code=400, 
            detail=f"Driver with primary number {driver_data.primary_number} is already registered. Please use a different number."
        )

    # Check for duplicate secondary number
    existing_secondary = db.query(CarDriver).filter(
        CarDriver.secondary_number == driver_data.secondary_number
    ).first()


    # Check for duplicate license number
    existing_license = db.query(CarDriver).filter(
        CarDriver.licence_number == driver_data.licence_number
    ).first()

    if existing_license:
        raise HTTPException(
            status_code=400, 
            detail=f"Driver with license number {driver_data.licence_number} is already registered. Please use a different license number."
        )

    # Hash password
    hashed_password = get_password_hash(driver_data.password)

    # Create car driver object
    car_driver = CarDriver(
        vehicle_owner_id=driver_data.vehicle_owner_id,
        organization_id=driver_data.organization_id,
        full_name=driver_data.full_name,
        primary_number=driver_data.primary_number,
        secondary_number=driver_data.secondary_number,
        hashed_password=hashed_password,
        licence_number=driver_data.licence_number,
        licence_front_img=None,  # Will be updated after GCS upload
        adress=driver_data.adress,
        driver_status=AccountStatusEnum.PROCESSING  # Explicitly set the enum value
    )

    db.add(car_driver)
    db.commit()
    db.refresh(car_driver)

    return car_driver

def update_driver_license_image(db: Session, driver_id: UUID, license_img_url: str) -> CarDriver:
    """Update the license front image URL for an existing car driver record"""
    from app.models.common_enums import DocumentStatusEnum
    
    driver = db.query(CarDriver).filter(
        CarDriver.id == driver_id
    ).first()
    
    if not driver:
        raise HTTPException(
            status_code=404, 
            detail=f"Car driver not found for ID: {driver_id}"
        )
    
    driver.licence_front_img = license_img_url
    driver.licence_front_status = DocumentStatusEnum.PENDING  # Set status to Pending when image is updated
    db.commit()
    db.refresh(driver)
    
    return driver

def get_driver_by_id(db: Session, driver_id: UUID) -> Optional[CarDriver]:
    """Get car driver by ID"""
    return db.query(CarDriver).filter(CarDriver.id == driver_id).first()

def get_drivers_by_organization(db: Session, organization_id: str) -> list[CarDriver]:
    """Get all drivers for a specific organization"""
    return db.query(CarDriver).filter(CarDriver.organization_id == organization_id).all()

def get_driver_by_mobile(db: Session, mobile_number: str) -> Optional[CarDriver]:
    """Get car driver by mobile number"""
    return db.query(CarDriver).filter(
        (CarDriver.primary_number == mobile_number) | 
        (CarDriver.secondary_number == mobile_number)
    ).first()

def get_drivers_by_vehicleOwner_id(db: Session, vehicle_owner_id: str) -> List[CarDriver]:
    return db.query(CarDriver).filter(CarDriver.vehicle_owner_id == vehicle_owner_id).all()


def get_available_drivers(db: Session, vehicle_owner_id: str) -> List[CarDriver]:
    """Get all available drivers with ONLINE status for a vehicle owner"""
    from app.models.car_driver import AccountStatusEnum
    return db.query(CarDriver).filter(
        CarDriver.vehicle_owner_id == vehicle_owner_id,
        CarDriver.driver_status.in_([AccountStatusEnum.ONLINE, AccountStatusEnum.DRIVING])
    ).all()

def authenticate_driver(db: Session, primary_number: str, password: str) -> Optional[CarDriver]:
    """Authenticate driver by primary number and password"""
    from app.core.security import verify_password
    
    driver = db.query(CarDriver).filter(CarDriver.primary_number == primary_number).first()
    
    if not driver:
        return None
    
    if not verify_password(password, driver.hashed_password):
        return None
    
    return driver

def update_driver_status(db: Session, driver_id: UUID, new_status: AccountStatusEnum) -> CarDriver:
    """Update driver's online/offline status with validation"""
    driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()
    
    if not driver:
        raise HTTPException(
            status_code=404, 
            detail=f"Driver not found for ID: {driver_id}"
        )
    
    # Validate status transitions
    current_status = driver.driver_status
    
    # Check if driver is trying to go online
    if new_status == AccountStatusEnum.ONLINE:
        if current_status != AccountStatusEnum.OFFLINE:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot set driver to ONLINE. Driver must be OFFLINE first. Current status: {current_status.value}"
            )
    
    # Check if driver is trying to go offline
    elif new_status == AccountStatusEnum.OFFLINE:
        if current_status not in [AccountStatusEnum.ONLINE, AccountStatusEnum.DRIVING]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot set driver to OFFLINE. Driver must be ONLINE or DRIVING first. Current status: {current_status.value}"
            )
    
    driver.driver_status = new_status
    db.commit()
    db.refresh(driver)
    
    return driver

def get_all_drivers(db: Session, vehicle_owner_id: str) -> List[CarDriver]:
    """Get all available drivers with ONLINE status for a vehicle owner"""
    from app.models.car_driver import AccountStatusEnum
    return db.query(CarDriver).filter(
        CarDriver.vehicle_owner_id == vehicle_owner_id
    ).all()