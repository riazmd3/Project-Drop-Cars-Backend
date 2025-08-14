from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.car_details import CarDetails
from app.schemas.car_details import CarDetailsForm
from typing import Optional
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
        organization_id=car_data.organization_id,
        car_name=car_data.car_name,
        car_type=car_data.car_type,
        car_number=car_data.car_number,
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
    car_details = db.query(CarDetails).filter(
        CarDetails.id == car_id
    ).first()
    
    if not car_details:
        raise HTTPException(
            status_code=404, 
            detail=f"Car details not found for ID: {car_id}"
        )
    
    # Update image URLs
    if 'rc_front_img_url' in image_urls:
        car_details.rc_front_img_url = image_urls['rc_front_img_url']
    if 'rc_back_img_url' in image_urls:
        car_details.rc_back_img_url = image_urls['rc_back_img_url']
    if 'insurance_img_url' in image_urls:
        car_details.insurance_img_url = image_urls['insurance_img_url']
    if 'fc_img_url' in image_urls:
        car_details.fc_img_url = image_urls['fc_img_url']
    if 'car_img_url' in image_urls:
        car_details.car_img_url = image_urls['car_img_url']
    
    db.commit()
    db.refresh(car_details)
    
    return car_details

def get_car_by_id(db: Session, car_id: UUID) -> Optional[CarDetails]:
    """Get car details by ID"""
    return db.query(CarDetails).filter(CarDetails.id == car_id).first()

def get_cars_by_organization(db: Session, organization_id: str) -> list[CarDetails]:
    """Get all cars for a specific organization"""
    return db.query(CarDetails).filter(CarDetails.organization_id == organization_id).all()
