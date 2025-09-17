from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.vendor import VendorCredentials
from app.models.vendor_details import VendorDetails
from app.schemas.vendor import VendorSignupForm
from app.core.security import get_password_hash, verify_password
from app.utils.gcs import upload_image_to_gcs, delete_gcs_file_by_url
from fastapi import UploadFile
import uuid

def create_vendor(db: Session, vendor_data: VendorSignupForm, aadhar_image: UploadFile = None):
    """
    Create a new vendor with both credentials and details
    Handles GCS image upload with rollback on failure
    """
    # Check if vendor already exists with the same primary number
    existing_vendor = db.query(VendorCredentials).filter(
        VendorCredentials.primary_number == vendor_data.primary_number
    ).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Vendor with this primary number already registered"
        )
    
    # Check if aadhar number already exists
    existing_aadhar = db.query(VendorDetails).filter(
        VendorDetails.aadhar_number == vendor_data.aadhar_number
    ).first()
    if existing_aadhar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Aadhar number already registered"
        )
    
    # Check if gpay number already exists
    existing_gpay = db.query(VendorDetails).filter(
        VendorDetails.gpay_number == vendor_data.gpay_number
    ).first()
    if existing_gpay:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="GPay number already registered"
        )
    
    aadhar_image_url = None
    
    try:
        # Upload image to GCS if provided
        if aadhar_image:
            aadhar_image_url = upload_image_to_gcs(aadhar_image, "vendor_details/aadhar")
        
        # Create vendor credentials
        hashed_password = get_password_hash(vendor_data.password)
        vendor_credentials = VendorCredentials(
            primary_number=vendor_data.primary_number,
            hashed_password=hashed_password
        )
        
        db.add(vendor_credentials)
        db.flush()  # Get the ID without committing
        
        # Create vendor details
        vendor_details = VendorDetails(
            vendor_id=vendor_credentials.id,
            full_name=vendor_data.full_name,
            primary_number=vendor_data.primary_number,
            secondary_number=vendor_data.secondary_number,
            gpay_number=vendor_data.gpay_number,
            aadhar_number=vendor_data.aadhar_number,
            aadhar_front_img=aadhar_image_url,
            adress=vendor_data.address,
            wallet_balance=0,
            bank_balance=0
        )
        
        db.add(vendor_details)
        db.commit()
        db.refresh(vendor_credentials)
        db.refresh(vendor_details)
        
        return vendor_credentials, vendor_details
        
    except Exception as e:
        # Rollback database changes
        db.rollback()
        
        # Delete uploaded image if database insertion failed
        if aadhar_image_url:
            delete_gcs_file_by_url(aadhar_image_url)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vendor: {str(e)}"
        )

def authenticate_vendor(db: Session, primary_number: str, password: str):
    """Authenticate vendor with primary number and password"""
    vendor = db.query(VendorCredentials).filter(
        VendorCredentials.primary_number == primary_number
    ).first()
    
    if not vendor or not verify_password(password, vendor.hashed_password):
        return None
    
    return vendor

def get_vendor_by_id(db: Session, vendor_id: str):
    """Get vendor by ID"""
    return db.query(VendorCredentials).filter(
        VendorCredentials.id == vendor_id
    ).first()

def get_vendor_details_by_vendor_id(db: Session, vendor_id: str):
    """Get vendor details by vendor ID"""
    return db.query(VendorDetails).filter(
        VendorDetails.vendor_id == vendor_id
    ).first()

def get_vendor_with_details(db: Session, vendor_id: str):
    """Get vendor credentials and details together"""
    vendor_credentials = get_vendor_by_id(db, vendor_id)
    vendor_details = get_vendor_details_by_vendor_id(db, vendor_id)
    
    if not vendor_credentials or not vendor_details:
        return None, None
    
    return vendor_credentials, vendor_details
