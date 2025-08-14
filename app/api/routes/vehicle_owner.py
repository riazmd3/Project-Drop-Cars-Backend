from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.vehicle_owner import VehicleOwnerBase, VehicleOwnerForm, UserLogin
from app.crud.vehicle_owner import create_user, update_aadhar_image, authenticate_user, get_vehicle_owner_counts
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url  # Utility functions
from app.core.security import create_access_token

router = APIRouter()

@router.post("/vehicleowner/signup")
async def signup(
    user_form: VehicleOwnerForm = Depends(VehicleOwnerForm.as_form),
    aadhar_front_img: UploadFile = File(..., description="Aadhar front image file"),
    db: Session = Depends(get_db),
):
    # Step 1: Validate form data using VehicleOwnerForm (FastAPI will return 422 if validation fails)
    
    # Step 1.5: Validate image file
    if not aadhar_front_img.content_type or not aadhar_front_img.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file (JPEG, PNG, etc.)"
        )
    
    # Check file size (limit to 5MB)
    if aadhar_front_img.size and aadhar_front_img.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=400,
            detail="Image file is too large. Please upload an image smaller than 5MB"
        )
    
    # Step 2: Create user in database first (without image)
    try:
        db_user = create_user(db, user_form)
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate mobile number, aadhar, etc.)
        raise
    except Exception as e:
        # Handle any other database errors
        raise HTTPException(
            status_code=500, 
            detail=f"Database error occurred while creating user: {str(e)}"
        )
    
    # Step 3: Only after successful DB commit, upload image to GCS
    try:
        aadhar_img_url = upload_image_to_gcs(aadhar_front_img)
    except Exception as e:
        # If GCS upload fails, we still have the user in DB but without image
        # You might want to delete the user or leave it as is depending on your requirements
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload image to cloud storage: {str(e)}. User created but image upload failed."
        )
    
    # Step 4: Update the database record with the GCS image URL
    try:
        update_aadhar_image(db, db_user.id, aadhar_img_url)
    except Exception as e:
        # If update fails, we have the image in GCS but not linked in DB
        # Clean up the uploaded image and raise error
        delete_gcs_file_by_url(aadhar_img_url)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to update user record with image URL: {str(e)}. Image uploaded but not linked to user."
        )

    return {
        "message": "Vehicle owner registered successfully", 
        "user_id": str(db_user.id), 
        "aadhar_img_url": aadhar_img_url,
        "status": "success"
    }


@router.post("/vehicleowner/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Get counts of related records
    counts = get_vehicle_owner_counts(db, db_user.id, db_user.organization_id)
    
    # Create access token
    access_token = create_access_token({"sub": str(db_user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "account_status": db_user.account_status.value,
        "car_driver_count": counts["car_driver_count"],
        "car_details_count": counts["car_details_count"]
    }
