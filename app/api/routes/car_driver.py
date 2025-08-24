from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.car_driver import CarDriverForm, CarDriverOut, CarDriverSignupResponse
from app.crud.car_driver import create_car_driver, update_driver_license_image
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url
from app.core.security import get_current_user
from app.models.vehicle_owner import VehicleOwnerCredentials
from typing import List

router = APIRouter()

@router.post("/cardriver/signup", response_model=CarDriverSignupResponse)
async def signup_car_driver(
    driver_form: CarDriverForm = Depends(CarDriverForm.as_form),
    licence_front_img: UploadFile = File(..., description="License front image file"),
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a new car driver with details and upload license image to GCS.
    Image is only uploaded after successful database insertion.
    """
    
    # Step 1: Validate license image file
    if not licence_front_img.content_type or not licence_front_img.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type for license image. Please upload an image file (JPEG, PNG, etc.)"
        )
    
    # Check file size (limit to 5MB)
    if licence_front_img.size and licence_front_img.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=400,
            detail="License image file is too large. Please upload an image smaller than 5MB"
        )
    
    # Step 2: Create car driver in database first (without image)
    # Set vehicle_owner_id and organization_id from authenticated user
    driver_form.vehicle_owner_id = driver_form.vehicle_owner_id
    if not driver_form.organization_id:
        driver_form.organization_id = current_user.organization_id
    
    try:
        db_driver = create_car_driver(db, driver_form)
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate mobile/license numbers, etc.)
        raise
    except Exception as e:
        # Handle any other database errors
        raise HTTPException(
            status_code=500, 
            detail=f"Database error occurred while creating car driver: {str(e)}"
        )
    
    # Step 3: Only after successful DB commit, upload license image to GCS
    try:
        # Create folder structure: car_driver/{driver_id}/license
        folder_path = f"car_driver/{db_driver.id}/license"
        license_img_url = upload_image_to_gcs(licence_front_img, folder_path)
    except Exception as e:
        # If GCS upload fails, we still have the driver in DB but without image
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload license image to cloud storage: {str(e)}. Driver created but image upload failed."
        )
    
    # Step 4: Update the database record with the GCS image URL
    try:
        update_driver_license_image(db, db_driver.id, license_img_url)
    except Exception as e:
        # If update fails, clean up the uploaded image and raise error
        delete_gcs_file_by_url(license_img_url)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update driver record with image URL: {str(e)}. Image uploaded but not linked to driver."
        )

    return {
        "message": "Car driver registered successfully", 
        "driver_id": str(db_driver.id), 
        "license_img_url": license_img_url,
        "status": "success"
    }

@router.get("/cardriver/{driver_id}", response_model=CarDriverOut)
def get_car_driver(
    driver_id: str, 
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get car driver by ID (only for authenticated vehicle owner)"""
    from app.crud.car_driver import get_driver_by_id
    from uuid import UUID
    
    try:
        driver_uuid = UUID(driver_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid driver ID format")
    
    driver = get_driver_by_id(db, driver_uuid)
    if not driver:
        raise HTTPException(status_code=404, detail="Car driver not found")
    
    # Verify that the driver belongs to the authenticated vehicle owner
    if driver.vehicle_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own drivers.")
    
    return driver

@router.get("/cardriver/organization/{organization_id}", response_model=List[CarDriverOut])
def get_drivers_by_organization(
    organization_id: str, 
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all drivers for a specific organization (only for authenticated vehicle owner)"""
    from app.crud.car_driver import get_drivers_by_organization
    
    # Verify that the organization_id matches the authenticated user's organization
    if organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view drivers from your own organization.")
    
    drivers = get_drivers_by_organization(db, organization_id)
    return drivers

@router.get("/cardriver/mobile/{mobile_number}", response_model=CarDriverOut)
def get_driver_by_mobile(
    mobile_number: str, 
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get car driver by mobile number (only for authenticated vehicle owner)"""
    from app.crud.car_driver import get_driver_by_mobile
    
    driver = get_driver_by_mobile(db, mobile_number)
    if not driver:
        raise HTTPException(status_code=404, detail="Car driver not found with this mobile number")
    
    # Verify that the driver belongs to the authenticated vehicle owner
    if driver.vehicle_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own drivers.")
    
    return driver
