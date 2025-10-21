from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.schemas.vendor import VendorSignupForm, VendorSignin, TokenResponse, VendorOut
from app.crud.vendor import create_vendor, authenticate_vendor, get_vendor_with_details, get_vendor_details_by_vendor_id
from app.core.security import create_access_token
from app.database.session import get_db
from typing import Optional
from app.schemas.vendor import VendorDetailsResponse
from app.core.security import get_current_vendor
from app.schemas.document_status import DocumentStatusListResponse, UpdateDocumentStatusRequest, UpdateDocumentRequest, DocumentUpdateResponse
from app.models.common_enums import DocumentStatusEnum

router = APIRouter()

@router.post("/vendor/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def vendor_signup(
    full_name: str = Form(..., description="Full name (3-100 characters)"),
    primary_number: str = Form(..., description="Primary mobile number"),
    secondary_number: Optional[str] = Form(None, description="Secondary mobile number (optional)"),
    password: str = Form(..., description="Password (min 6 characters)"),
    address: str = Form(..., description="Address (min 10 characters)"),
    aadhar_number: str = Form(..., description="Aadhar number (12 digits)"),
    gpay_number: str = Form(..., description="GPay number"),
    aadhar_image: Optional[UploadFile] = File(None, description="Aadhar front image"),
    db: Session = Depends(get_db)
):
    """
    Vendor Signup API
    
    Creates a new vendor account with both credentials and details.
    Uploads aadhar image to GCS and stores the URL in database.
    Implements rollback mechanism - if database insertion fails, 
    the uploaded image is deleted from GCS.
    
    Returns:
        - Access token for authentication
        - Vendor details
    """
    try:
        # Validate form data
        vendor_data = VendorSignupForm(
            full_name=full_name,
            primary_number=primary_number,
            secondary_number=secondary_number,
            password=password,
            address=address,
            aadhar_number=aadhar_number,
            gpay_number=gpay_number
        )
        
        # Validate image file if provided
        if aadhar_image:
            if not aadhar_image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be an image"
                )
            
            # Check file size (max 5MB)
            if aadhar_image.size and aadhar_image.size > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image size must be less than 5MB"
                )
        
        # Create vendor
        vendor_credentials, vendor_details = create_vendor(db, vendor_data, aadhar_image)
        
        # Create access token
        access_token = create_access_token({"sub": str(vendor_credentials.id)})
        
        # Prepare response
        vendor_response = VendorOut(
            id=vendor_details.id,
            full_name=vendor_details.full_name,
            primary_number=vendor_details.primary_number,
            secondary_number=vendor_details.secondary_number,
            gpay_number=vendor_details.gpay_number,
            wallet_balance=vendor_details.wallet_balance,
            bank_balance=vendor_details.bank_balance,
            aadhar_number=vendor_details.aadhar_number,
            aadhar_front_img=vendor_details.aadhar_front_img,
            address=vendor_details.adress,
            account_status=vendor_credentials.account_status.value,
            created_at=vendor_details.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            vendor=vendor_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/vendor/signin", response_model=TokenResponse)
async def vendor_signin(
    vendor_data: VendorSignin,
    db: Session = Depends(get_db)
):
    """
    Vendor Signin API
    
    Authenticates vendor with primary number and password.
    Returns access token and vendor details upon successful authentication.
    
    Returns:
        - Access token for authentication
        - Vendor details
    """
    try:
        # Authenticate vendor
        vendor_credentials = authenticate_vendor(
            db, 
            vendor_data.primary_number, 
            vendor_data.password
        )
        
        if not vendor_credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid primary number or password"
            )
        
        # Get vendor details
        vendor_details = get_vendor_with_details(db, str(vendor_credentials.id))[1]
        
        if not vendor_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor details not found"
            )
        
        # Create access token
        access_token = create_access_token({"sub": str(vendor_credentials.id),"token_version" : vendor_credentials.token_version,"user":"vendor"})
        
        # Prepare response
        vendor_response = VendorOut(
            id=vendor_details.id,
            full_name=vendor_details.full_name,
            primary_number=vendor_details.primary_number,
            secondary_number=vendor_details.secondary_number,
            gpay_number=vendor_details.gpay_number,
            wallet_balance=vendor_details.wallet_balance,
            bank_balance=vendor_details.bank_balance,
            aadhar_number=vendor_details.aadhar_number,
            aadhar_front_img=vendor_details.aadhar_front_img,
            address=vendor_details.adress,
            account_status=vendor_credentials.account_status.value,
            created_at=vendor_details.created_at
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            vendor=vendor_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/vendor-details/me", response_model=VendorDetailsResponse)
def get_my_vendor_details(
    db: Session = Depends(get_db),
    vendor_id: str = Depends(get_current_vendor),
):
    # Unpack both credentials and details from the DB
    vendor_credentials, vendor_details = get_vendor_with_details(db, str(vendor_id.id))

    return VendorDetailsResponse(
        id=str(vendor_details.id),
        address=vendor_details.adress,  # mapping from 'adress' in DB
        account_status=vendor_credentials.account_status.value,
        full_name=vendor_details.full_name,
        primary_number=vendor_details.primary_number,
        secondary_number=vendor_details.secondary_number,
        gpay_number=vendor_details.gpay_number,
        wallet_balance=vendor_details.wallet_balance,
        bank_balance=vendor_details.bank_balance,
        aadhar_number=vendor_details.aadhar_number,
        aadhar_front_img=vendor_details.aadhar_front_img,
        created_at=vendor_details.created_at,
    )


@router.get("/vendor/document-status", response_model=DocumentStatusListResponse)
def get_vendor_document_status(
    db: Session = Depends(get_db),
    vendor_id: str = Depends(get_current_vendor),
):
    """Get document status for vendor"""
    vendor_credentials, vendor_details = get_vendor_with_details(db, str(vendor_id.id))
    
    if not vendor_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor details not found"
        )
    
    documents = {}
    if vendor_details.aadhar_front_img:
        documents["aadhar"] = {
            "document_type": "aadhar",
            "status": vendor_details.aadhar_status.value if vendor_details.aadhar_status else "Pending",
            "image_url": vendor_details.aadhar_front_img,
            "updated_at": None
        }
    
    return DocumentStatusListResponse(
        entity_id=vendor_details.id,
        entity_type="vendor",
        documents=documents
    )


@router.patch("/vendor/document-status", response_model=DocumentUpdateResponse)
def update_vendor_document_status(
    status_update: UpdateDocumentStatusRequest,
    db: Session = Depends(get_db),
    vendor_id: str = Depends(get_current_vendor),
):
    """Update document status for vendor (admin only)"""
    vendor_credentials, vendor_details = get_vendor_with_details(db, str(vendor_id.id))
    
    if not vendor_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor details not found"
        )
    
    # Update aadhar status
    vendor_details.aadhar_status = status_update.status
    db.commit()
    db.refresh(vendor_details)
    
    return DocumentUpdateResponse(
        message="Document status updated successfully",
        document_type="aadhar",
        new_image_url=vendor_details.aadhar_front_img,
        new_status=status_update.status.value
    )


@router.post("/vendor/update-document", response_model=DocumentUpdateResponse)
async def update_vendor_document(
    document_type: str = Form(...),
    aadhar_image: UploadFile = File(...),
    db: Session = Depends(get_db),
    vendor_id: str = Depends(get_current_vendor),
):
    """Update vendor document (upload new image)"""
    if document_type != "aadhar":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document type for vendor"
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
    
    vendor_credentials, vendor_details = get_vendor_with_details(db, str(vendor_id.id))
    
    if not vendor_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor details not found"
        )
    
    # Upload new image to GCS
    from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url
    
    try:
        # Delete old image if exists
        if vendor_details.aadhar_front_img:
            delete_gcs_file_by_url(vendor_details.aadhar_front_img)
        
        # Upload new image
        new_image_url = upload_image_to_gcs(aadhar_image, "vendor_details/aadhar")
        
        # Update database
        vendor_details.aadhar_front_img = new_image_url
        vendor_details.aadhar_status = DocumentStatusEnum.PENDING
        db.commit()
        db.refresh(vendor_details)
        
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