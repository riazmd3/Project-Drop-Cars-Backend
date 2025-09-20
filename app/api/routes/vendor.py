from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.schemas.vendor import VendorSignupForm, VendorSignin, TokenResponse, VendorOut
from app.crud.vendor import create_vendor, authenticate_vendor, get_vendor_with_details
from app.core.security import create_access_token
from app.database.session import get_db
from typing import Optional

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
