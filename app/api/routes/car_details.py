from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.car_details import CarDetailsForm, CarDetailsOut, CarDetailsSignupResponse
from app.crud.car_details import create_car_details, update_car_images
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url
from typing import List

router = APIRouter()

@router.post("/cardetails/signup", response_model=CarDetailsSignupResponse)
async def signup_car_details(
    car_form: CarDetailsForm = Depends(CarDetailsForm.as_form),
    rc_front_img: UploadFile = File(..., description="RC Front image file"),
    rc_back_img: UploadFile = File(..., description="RC Back image file"),
    insurance_img: UploadFile = File(..., description="Insurance image file"),
    fc_img: UploadFile = File(..., description="FC image file"),
    car_img: UploadFile = File(..., description="Car image file"),
    db: Session = Depends(get_db),
):
    """
    Register a new car with details and upload all required images to GCS.
    Images are only uploaded after successful database insertion.
    """
    
    # Step 1: Validate all image files
    image_files = {
        'rc_front_img': rc_front_img,
        'rc_back_img': rc_back_img,
        'insurance_img': insurance_img,
        'fc_img': fc_img,
        'car_img': car_img
    }
    
    for field_name, image_file in image_files.items():
        if not image_file.content_type or not image_file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {field_name}. Please upload an image file (JPEG, PNG, etc.)"
            )
        
        # Check file size (limit to 5MB)
        if image_file.size and image_file.size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} file is too large. Please upload an image smaller than 5MB"
            )
    
    # Step 2: Create car details in database first (without images)
    try:
        db_car = create_car_details(db, car_form)
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate car number, etc.)
        raise
    except Exception as e:
        # Handle any other database errors
        raise HTTPException(
            status_code=500, 
            detail=f"Database error occurred while creating car details: {str(e)}"
        )
    
    # Step 3: Only after successful DB commit, upload images to GCS
    uploaded_urls = {}
    uploaded_files = []  # Track successfully uploaded files for cleanup if needed
    
    try:
        # Upload each image to GCS with car-specific folder structure
        for field_name, image_file in image_files.items():
            # Create folder structure: car_details/{car_id}/{image_type}
            folder_path = f"car_details/{db_car.id}/{field_name}"
            image_url = upload_image_to_gcs(image_file, folder_path)
            uploaded_urls[f"{field_name}_url"] = image_url
            uploaded_files.append(image_url)
            
    except Exception as e:
        # If GCS upload fails, clean up any uploaded files and raise error
        for uploaded_url in uploaded_files:
            try:
                delete_gcs_file_by_url(uploaded_url)
            except:
                pass  # Ignore cleanup errors
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload images to cloud storage: {str(e)}. Car details created but image upload failed."
        )
    
    # Step 4: Update the database record with the GCS image URLs
    try:
        update_car_images(db, db_car.id, uploaded_urls)
    except Exception as e:
        # If update fails, clean up uploaded images and raise error
        for uploaded_url in uploaded_files:
            try:
                delete_gcs_file_by_url(uploaded_url)
            except:
                pass  # Ignore cleanup errors
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update car record with image URLs: {str(e)}. Images uploaded but not linked to car."
        )

    return {
        "message": "Car details registered successfully", 
        "car_id": str(db_car.id), 
        "image_urls": uploaded_urls,
        "status": "success"
    }

@router.get("/cardetails/{car_id}", response_model=CarDetailsOut)
def get_car_details(car_id: str, db: Session = Depends(get_db)):
    """Get car details by ID"""
    from app.crud.car_details import get_car_by_id
    from uuid import UUID
    
    try:
        car_uuid = UUID(car_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid car ID format")
    
    car = get_car_by_id(db, car_uuid)
    if not car:
        raise HTTPException(status_code=404, detail="Car details not found")
    
    return car

@router.get("/cardetails/organization/{organization_id}", response_model=List[CarDetailsOut])
def get_cars_by_organization(organization_id: str, db: Session = Depends(get_db)):
    """Get all cars for a specific organization"""
    from app.crud.car_details import get_cars_by_organization
    
    cars = get_cars_by_organization(db, organization_id)
    return cars
