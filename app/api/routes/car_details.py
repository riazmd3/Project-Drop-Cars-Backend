from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.schemas.car_details import CarDetailsForm, CarDetailsOut, CarDetailsSignupResponse
from app.crud.car_details import create_car_details, update_car_images
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url
from app.core.security import get_current_user
from app.models.vehicle_owner import VehicleOwnerCredentials
from typing import List
from app.schemas.document_status import DocumentStatusListResponse, UpdateDocumentStatusRequest, UpdateDocumentRequest, DocumentUpdateResponse
from app.models.common_enums import DocumentStatusEnum

router = APIRouter()

@router.post("/cardetails/signup", response_model=CarDetailsSignupResponse)
async def signup_car_details(
    car_form: CarDetailsForm = Depends(CarDetailsForm.as_form),
    rc_front_img: UploadFile = File(..., description="RC Front image file"),
    rc_back_img: UploadFile = File(..., description="RC Back image file"),
    insurance_img: UploadFile = File(..., description="Insurance image file"),
    fc_img: UploadFile = File(..., description="FC image file"),
    car_img: UploadFile = File(..., description="Car image file"),
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
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
    # Set vehicle_owner_id from authenticated user
    car_form.vehicle_owner_id = car_form.vehicle_owner_id
    
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
def get_car_details(
    car_id: str, 
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get car details by ID (only for authenticated vehicle owner)"""
    from app.crud.car_details import get_car_by_id
    from uuid import UUID
    
    try:
        car_uuid = UUID(car_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid car ID format")
    
    car = get_car_by_id(db, car_uuid)
    if not car:
        raise HTTPException(status_code=404, detail="Car details not found")
    
    # Verify that the car belongs to the authenticated vehicle owner
    if car.vehicle_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own cars.")
    
    return car

@router.get("/cardetails/all", response_model=List[CarDetailsOut])
def get_all_cars(
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all cars for the authenticated vehicle owner"""
    from app.crud.car_details import get_all_cars
    
    cars = get_all_cars(db, str(current_user.id))
    return cars


@router.get("/cardetails/{car_id}/document-status", response_model=DocumentStatusListResponse)
def get_car_document_status(
    car_id: str,
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document status for car"""
    from app.crud.car_details import get_car_by_id
    from uuid import UUID
    
    try:
        car_uuid = UUID(car_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid car ID format")
    
    car = get_car_by_id(db, car_uuid)
    if not car:
        raise HTTPException(status_code=404, detail="Car details not found")
    
    # Verify that the car belongs to the authenticated vehicle owner
    if car.vehicle_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own cars.")
    
    documents = {}
    if car.rc_front_img_url:
        documents["rc_front"] = {
            "document_type": "rc_front",
            "status": car.rc_front_status.value if car.rc_front_status else "Pending",
            "image_url": car.rc_front_img_url,
            "updated_at": None
        }
    if car.rc_back_img_url:
        documents["rc_back"] = {
            "document_type": "rc_back",
            "status": car.rc_back_status.value if car.rc_back_status else "Pending",
            "image_url": car.rc_back_img_url,
            "updated_at": None
        }
    if car.insurance_img_url:
        documents["insurance"] = {
            "document_type": "insurance",
            "status": car.insurance_status.value if car.insurance_status else "Pending",
            "image_url": car.insurance_img_url,
            "updated_at": None
        }
    if car.fc_img_url:
        documents["fc"] = {
            "document_type": "fc",
            "status": car.fc_status.value if car.fc_status else "Pending",
            "image_url": car.fc_img_url,
            "updated_at": None
        }
    if car.car_img_url:
        documents["car_img"] = {
            "document_type": "car_img",
            "status": car.car_img_status.value if car.car_img_status else "Pending",
            "image_url": car.car_img_url,
            "updated_at": None
        }
    
    return DocumentStatusListResponse(
        entity_id=car.id,
        entity_type="car",
        documents=documents
    )


@router.patch("/cardetails/{car_id}/document-status", response_model=DocumentUpdateResponse)
def update_car_document_status(
    car_id: str,
    document_type: str,
    status_update: UpdateDocumentStatusRequest,
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update document status for car (admin only)"""
    from app.crud.car_details import get_car_by_id
    from uuid import UUID
    
    try:
        car_uuid = UUID(car_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid car ID format")
    
    car = get_car_by_id(db, car_uuid)
    if not car:
        raise HTTPException(status_code=404, detail="Car details not found")
    
    # Verify that the car belongs to the authenticated vehicle owner
    if car.vehicle_owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own cars.")
    
    # Update specific document status
    if document_type == "rc_front":
        car.rc_front_status = status_update.status
    elif document_type == "rc_back":
        car.rc_back_status = status_update.status
    elif document_type == "insurance":
        car.insurance_status = status_update.status
    elif document_type == "fc":
        car.fc_status = status_update.status
    elif document_type == "car_img":
        car.car_img_status = status_update.status
    else:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    db.commit()
    db.refresh(car)
    
    return DocumentUpdateResponse(
        message="Document status updated successfully",
        document_type=document_type,
        new_image_url=getattr(car, f"{document_type}_img_url"),
        new_status=status_update.status.value
    )


@router.post("/cardetails/{car_id}/update-document", response_model=DocumentUpdateResponse)
async def update_car_document(
    car_id: str,
    document_type: str = Form(...),
    image: UploadFile = File(...),
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update car document (upload new image)"""
    from app.crud.car_details import get_car_by_id
    from uuid import UUID
    
    try:
        car_uuid = UUID(car_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid car ID format")
    
    car = get_car_by_id(db, car_uuid)
    if not car:
        raise HTTPException(status_code=404, detail="Car details not found")
    
    # Verify that the car belongs to the authenticated vehicle owner
    if car.vehicle_owner_id != current_user.vehicle_owner_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own cars.")
    
    valid_document_types = ["rc_front", "rc_back", "insurance", "fc", "car"]
    if document_type not in valid_document_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_document_types)}"
        )
    
    # Validate image file
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an image file"
        )
    
    if image.size and image.size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=400,
            detail="Image file is too large. Please upload an image smaller than 5MB"
        )
    
    try:
        # Delete old image if exists
        old_image_url = getattr(car, f"{document_type}_img_url")
        if old_image_url:
            delete_gcs_file_by_url(old_image_url)
        
        # Upload new image
        folder_path = f"car_details/{car.id}/{document_type}"
        new_image_url = upload_image_to_gcs(image, folder_path)
        
        # Update database
        setattr(car, f"{document_type}_img_url", new_image_url)
        setattr(car, f"{document_type}_status", DocumentStatusEnum.PENDING) if document_type != "car" else setattr(car, f"{document_type}img_status", DocumentStatusEnum.PENDING)
        db.commit()
        db.refresh(car)
        
        return DocumentUpdateResponse(
            message="Document updated successfully",
            document_type=document_type,
            new_image_url=new_image_url,
            new_status="Pending"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update document: {str(e)}"
        )


@router.get("/cardetails/all-document-status", response_model=List[DocumentStatusListResponse])
def get_all_cars_document_status(
    current_user: VehicleOwnerCredentials = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document status for all cars belonging to vehicle owner"""
    from app.crud.car_details import get_all_cars
    
    cars = get_all_cars(db, str(current_user.id))
    
    car_statuses = []
    for car in cars:
        documents = {}
        if car.rc_front_img_url:
            documents["rc_front"] = {
                "document_type": "rc_front",
                "status": car.rc_front_status.value if car.rc_front_status else "Pending",
                "image_url": car.rc_front_img_url,
                "updated_at": None
            }
        if car.rc_back_img_url:
            documents["rc_back"] = {
                "document_type": "rc_back",
                "status": car.rc_back_status.value if car.rc_back_status else "Pending",
                "image_url": car.rc_back_img_url,
                "updated_at": None
            }
        if car.insurance_img_url:
            documents["insurance"] = {
                "document_type": "insurance",
                "status": car.insurance_status.value if car.insurance_status else "Pending",
                "image_url": car.insurance_img_url,
                "updated_at": None
            }
        if car.fc_img_url:
            documents["fc"] = {
                "document_type": "fc",
                "status": car.fc_status.value if car.fc_status else "Pending",
                "image_url": car.fc_img_url,
                "updated_at": None
            }
        if car.car_img_url:
            documents["car_img"] = {
                "document_type": "car_img",
                "status": car.car_img_status.value if car.car_img_status else "Pending",
                "image_url": car.car_img_url,
                "updated_at": None
            }
        
        car_statuses.append(DocumentStatusListResponse(
            entity_id=car.id,
            entity_type="car",
            documents=documents
        ))
    
    return car_statuses
