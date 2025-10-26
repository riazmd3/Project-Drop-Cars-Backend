from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.vehicle_owner import VehicleOwnerBase, VehicleOwnerForm, UserLogin, VehicleOwnerDetailsResponse
from app.crud.vehicle_owner import create_user, update_aadhar_image, authenticate_user, get_vehicle_owner_counts, get_vehicle_owner_by_id
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url  # Utility functions
from app.core.security import create_access_token, get_current_vehicleOwner_id,get_current_user
from app.schemas.document_status import DocumentStatusListResponse, UpdateDocumentStatusRequest, UpdateDocumentRequest, DocumentUpdateResponse
from app.models.common_enums import DocumentStatusEnum
from typing import List

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
    counts = get_vehicle_owner_counts(db, db_user.id)
    
    # Create access token
    access_token = create_access_token({"sub": str(db_user.id),"user":"vehicle_owner"})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "account_status": db_user.account_status.value,
        "car_driver_count": counts["car_driver_count"],
        "car_details_count": counts["car_details_count"]
    }

@router.get("/vehicle-owner/me", response_model=VehicleOwnerDetailsResponse)
def get_my_vehicle_owner_details(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    owner = get_vehicle_owner_by_id(db, vehicle_owner_id)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner not found"
        )
    return owner

@router.get("/available-cars")
async def get_all_cars(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all available cars with ONLINE status for the authenticated vehicle owner"""
    # Get vehicle_owner_id from the authenticated user
    vehicle_owner_id = str(current_user.vehicle_owner_id)
    
    from app.crud.car_details import get_all_cars
    available_cars = get_all_cars(db, vehicle_owner_id)
    return available_cars

@router.get("/available-drivers")
async def get_available_drivers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get all available drivers with ONLINE status for the authenticated vehicle owner"""
    # Get vehicle_owner_id from the authenticated user
    vehicle_owner_id = str(current_user.vehicle_owner_id)
    
    from app.crud.car_driver import get_all_drivers
    available_drivers = get_all_drivers(db, vehicle_owner_id)
    return available_drivers


@router.get("/vehicle-owner/document-status", response_model=DocumentStatusListResponse)
def get_vehicle_owner_document_status(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """Get document status for vehicle owner"""
    owner_details = get_vehicle_owner_by_id(db, vehicle_owner_id)
    
    if not owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner details not found"
        )
    
    documents = {}
    if owner_details.aadhar_front_img:
        documents["aadhar"] = {
            "document_type": "aadhar",
            "status": owner_details.aadhar_status.value if owner_details.aadhar_status else "Pending",
            "image_url": owner_details.aadhar_front_img,
            "updated_at": None
        }
    
    return DocumentStatusListResponse(
        entity_id=owner_details.vehicle_owner_id,
        entity_type="vehicle_owner",
        documents=documents
    )


@router.patch("/vehicle-owner/document-status", response_model=DocumentUpdateResponse)
def update_vehicle_owner_document_status(
    status_update: UpdateDocumentStatusRequest,
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """Update document status for vehicle owner (admin only)"""
    owner_details = get_vehicle_owner_by_id(db, vehicle_owner_id)
    
    if not owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner details not found"
        )
    
    # Update aadhar status
    owner_details.aadhar_status = status_update.status
    db.commit()
    db.refresh(owner_details)
    
    return DocumentUpdateResponse(
        message="Document status updated successfully",
        document_type="aadhar",
        new_image_url=owner_details.aadhar_front_img,
        new_status=status_update.status.value
    )


@router.post("/vehicle-owner/update-document", response_model=DocumentUpdateResponse)
async def update_vehicle_owner_document(
    document_type: str = Form(...),
    aadhar_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """Update vehicle owner document (upload new image)"""
    if document_type != "aadhar":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type for vehicle owner"
        )
    
    # Validate image file
    if not aadhar_image.content_type or not aadhar_image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image file"
        )
    
    if aadhar_image.size and aadhar_image.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is too large. Please upload an image smaller than 5MB"
        )
    
    owner_details = get_vehicle_owner_by_id(db, vehicle_owner_id)
    
    if not owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner details not found"
        )
    
    try:
        # Delete old image if exists
        if owner_details.aadhar_front_img:
            delete_gcs_file_by_url(owner_details.aadhar_front_img)
        
        # Upload new image
        new_image_url = upload_image_to_gcs(aadhar_image, "vehicle_owner_details/aadhar")
        
        # Update database
        owner_details.aadhar_front_img = new_image_url
        owner_details.aadhar_status = DocumentStatusEnum.PENDING
        db.commit()
        db.refresh(owner_details)
        
        return DocumentUpdateResponse(
            message="Document updated successfully",
            document_type="aadhar",
            new_image_url=new_image_url,
            new_status="Pending"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )


@router.get("/vehicle-owner/all-document-status", response_model=List[DocumentStatusListResponse])
def get_all_document_statuses(
    db: Session = Depends(get_db),
    vehicle_owner_id: str = Depends(get_current_vehicleOwner_id),
):
    """Get document status for all entities (vehicle owner, cars, drivers) belonging to vehicle owner"""
    from app.crud.car_details import get_all_cars
    from app.crud.car_driver import get_drivers_by_vehicleOwner_id
    
    all_statuses = []
    
    # 1. Get vehicle owner's own document status
    owner_details = get_vehicle_owner_by_id(db, vehicle_owner_id)
    if owner_details and owner_details.aadhar_front_img:
        owner_documents = {
            "aadhar": {
                "document_type": "aadhar",
                "status": owner_details.aadhar_status.value if owner_details.aadhar_status else "Pending",
                "image_url": owner_details.aadhar_front_img,
                "updated_at": None
            }
        }
        all_statuses.append(DocumentStatusListResponse(
            entity_id=owner_details.vehicle_owner_id,
            entity_type="vehicle_owner",
            documents=owner_documents
        ))
    
    # 2. Get all cars' document statuses
    cars = get_all_cars(db, str(vehicle_owner_id))
    for car in cars:
        car_documents = {}
        if car.rc_front_img_url:
            car_documents["rc_front"] = {
                "document_type": "rc_front",
                "status": car.rc_front_status.value if car.rc_front_status else "Pending",
                "image_url": car.rc_front_img_url,
                "updated_at": None
            }
        if car.rc_back_img_url:
            car_documents["rc_back"] = {
                "document_type": "rc_back",
                "status": car.rc_back_status.value if car.rc_back_status else "Pending",
                "image_url": car.rc_back_img_url,
                "updated_at": None
            }
        if car.insurance_img_url:
            car_documents["insurance"] = {
                "document_type": "insurance",
                "status": car.insurance_status.value if car.insurance_status else "Pending",
                "image_url": car.insurance_img_url,
                "updated_at": None
            }
        if car.fc_img_url:
            car_documents["fc"] = {
                "document_type": "fc",
                "status": car.fc_status.value if car.fc_status else "Pending",
                "image_url": car.fc_img_url,
                "updated_at": None
            }
        if car.car_img_url:
            car_documents["car_img"] = {
                "document_type": "car_img",
                "status": car.car_img_status.value if car.car_img_status else "Pending",
                "image_url": car.car_img_url,
                "updated_at": None
            }
        
        all_statuses.append(DocumentStatusListResponse(
            entity_id=car.id,
            entity_type="car",
            documents=car_documents
        ))
    
    # 3. Get all drivers' document statuses
    drivers = get_drivers_by_vehicleOwner_id(db, str(vehicle_owner_id))
    for driver in drivers:
        driver_documents = {}
        if driver.licence_front_img:
            driver_documents["licence"] = {
                "document_type": "licence",
                "status": driver.licence_front_status.value if driver.licence_front_status else "Pending",
                "image_url": driver.licence_front_img,
                "updated_at": None
            }
        
        all_statuses.append(DocumentStatusListResponse(
            entity_id=driver.id,
            entity_type="driver",
            documents=driver_documents
        ))
    
    return all_statuses