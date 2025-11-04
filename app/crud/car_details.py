from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.car_details import CarDetails
from app.schemas.car_details import CarDetailsForm
from typing import Optional, List
from uuid import UUID

def create_car_details(db: Session, car_data: CarDetailsForm) -> CarDetails:
    """Create a new car details record in the database"""
    
    # Check for duplicate car number
    existing_car = db.query(CarDetails).filter(
        CarDetails.car_number == car_data.car_number
    ).first()

    if existing_car:
        raise HTTPException(
            status_code=400, 
            detail=f"Car with registration number {car_data.car_number} is already registered. Please use a different number."
        )

    # Create car details object
    car_details = CarDetails(
        vehicle_owner_id=car_data.vehicle_owner_id,
        car_name=car_data.car_name,
        car_type=car_data.car_type,
        car_number=car_data.car_number,
        year_of_the_car=car_data.year_of_the_car,
        rc_front_img_url=None,  # Will be updated after GCS upload
        rc_back_img_url=None,   # Will be updated after GCS upload
        insurance_img_url=None, # Will be updated after GCS upload
        fc_img_url=None,        # Will be updated after GCS upload
        car_img_url=None        # Will be updated after GCS upload
    )

    db.add(car_details)
    db.commit()
    db.refresh(car_details)

    return car_details

def update_car_images(db: Session, car_id: UUID, image_urls: dict) -> CarDetails:
    """Update the image URLs for an existing car details record"""
    from app.models.common_enums import DocumentStatusEnum
    
    car_details = db.query(CarDetails).filter(
        CarDetails.id == car_id
    ).first()
    
    if not car_details:
        raise HTTPException(
            status_code=404, 
            detail=f"Car details not found for ID: {car_id}"
        )
    
    # Update image URLs and set status to Pending for updated images
    if 'rc_front_img_url' in image_urls:
        car_details.rc_front_img_url = image_urls['rc_front_img_url']
        car_details.rc_front_status = DocumentStatusEnum.PENDING
    if 'rc_back_img_url' in image_urls:
        car_details.rc_back_img_url = image_urls['rc_back_img_url']
        car_details.rc_back_status = DocumentStatusEnum.PENDING
    if 'insurance_img_url' in image_urls:
        car_details.insurance_img_url = image_urls['insurance_img_url']
        car_details.insurance_status = DocumentStatusEnum.PENDING
    if 'fc_img_url' in image_urls:
        car_details.fc_img_url = image_urls['fc_img_url']
        car_details.fc_status = DocumentStatusEnum.PENDING
    if 'car_img_url' in image_urls:
        car_details.car_img_url = image_urls['car_img_url']
        car_details.car_img_status = DocumentStatusEnum.PENDING
    if 'permit_img_url' in image_urls:
        car_details.permit_img_url = image_urls['permit_img_url']
        car_details.permit_status = DocumentStatusEnum.PENDING
    
    db.commit()
    db.refresh(car_details)
    
    return car_details

def get_car_by_id(db: Session, car_id: UUID) -> Optional[CarDetails]:
    """Get car details by ID"""
    return db.query(CarDetails).filter(CarDetails.id == car_id).first()


def get_car_detail_by_id(db: Session, car_id: UUID) -> Optional[CarDetails]:
    return db.query(CarDetails).filter(CarDetails.id == car_id).first()


def get_available_cars(db: Session, vehicle_owner_id: str) -> List[CarDetails]:
    """Get all available cars with ONLINE status for a vehicle owner"""
    from app.models.car_details import CarStatusEnum
    return db.query(CarDetails).filter(
        CarDetails.vehicle_owner_id == vehicle_owner_id,
        CarDetails.car_status.in_([CarStatusEnum.ONLINE, CarStatusEnum.DRIVING])
    ).all()

def get_all_cars(db: Session, vehicle_owner_id: str) -> List[CarDetails]:
    """Get all available cars with ONLINE status for a vehicle owner"""
    from app.models.car_details import CarStatusEnum
    return db.query(CarDetails).filter(
        CarDetails.vehicle_owner_id == vehicle_owner_id
    ).all()