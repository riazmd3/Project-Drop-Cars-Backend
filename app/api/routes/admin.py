# api/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.schemas.admin import AdminSignup, AdminSignin, AdminTokenResponse, AdminOut, AdminUpdate
from app.schemas.admin_add_money import VehicleOwnerInfoResponse, SearchVehicleOwnerRequest, AdminAddMoneyRequest, AdminAddMoneyResponse
from app.crud.admin import create_admin, authenticate_admin, get_admin_by_id, update_admin, get_all_admins
from app.crud.admin_add_money import get_vehicle_owner_by_primary_number, create_admin_add_money_transaction
from app.crud.admin_management import (
    get_all_vendors, get_vendor_full_details, update_vendor_account_status, update_vendor_document_status,
    get_all_vehicle_owners, get_vehicle_owner_full_details, update_vehicle_owner_account_status,
    update_vehicle_owner_document_status, get_vehicle_owner_cars, get_vehicle_owner_drivers,
    update_car_account_status, update_car_document_status, update_driver_account_status, update_driver_document_status
)
from app.schemas.admin_management import (
    VendorListOut, VendorFullDetailsResponse, VehicleOwnerListOut, VehicleOwnerFullDetailsResponse,
    UpdateAccountStatusRequest, UpdateDocumentStatusRequest, StatusUpdateResponse,
    CarListResponse, DriverListResponse, VehicleOwnerWithAssetsResponse
)
from app.core.security import create_access_token, get_current_admin
from app.database.session import get_db
from app.utils.gcs import upload_image_to_gcs, generate_signed_url_from_gcs
from app.models.common_enums import DocumentStatusEnum
from typing import List, Optional
from uuid import UUID
import os

router = APIRouter()

@router.post("/admin/signup", response_model=AdminTokenResponse, status_code=status.HTTP_201_CREATED)
async def admin_signup(
    admin_data: AdminSignup,
    db: Session = Depends(get_db)
):
    """
    Admin Signup API
    
    Creates a new admin account with credentials.
    Returns JWT access token for authentication.
    
    Returns:
        - Access token for authentication
        - Admin details
    """
    try:
        # Check if admin already exists with the same username
        from app.crud.admin import get_admin_by_username
        existing_admin = get_admin_by_username(db, admin_data.username)
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Admin with this username already registered"
            )
        
        # Check if admin already exists with the same email
        from app.crud.admin import get_admin_by_email
        existing_email = get_admin_by_email(db, admin_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Admin with this email already registered"
            )
        
        # Check if admin already exists with the same phone
        from app.crud.admin import get_admin_by_phone
        existing_phone = get_admin_by_phone(db, admin_data.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Admin with this phone number already registered"
            )
        
        # Hash password and create admin
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(admin_data.password)
        
        admin = create_admin(
            db=db,
            username=admin_data.username,
            hashed_password=hashed_password,
            role=admin_data.role,
            email=admin_data.email,
            phone=admin_data.phone
        )
        
        # Create access token
        access_token = create_access_token({"sub": str(admin.id)})
        
        # Prepare response
        admin_response = AdminOut(
            id=admin.id,
            username=admin.username,
            email=admin.email,
            phone=admin.phone,
            role=admin.role,
            organization_id=admin.organization_id,
            created_at=admin.created_at
        )
        
        return AdminTokenResponse(
            access_token=access_token,
            token_type="bearer",
            admin=admin_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/admin/signin", response_model=AdminTokenResponse)
async def admin_signin(
    admin_data: AdminSignin,
    db: Session = Depends(get_db)
):
    """
    Admin Signin API
    
    Authenticates admin with username and password.
    Returns JWT access token upon successful authentication.
    
    Returns:
        - Access token for authentication
        - Admin details
    """
    try:
        # Authenticate admin
        admin = authenticate_admin(db, admin_data.username, admin_data.password)
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token = create_access_token({"sub": str(admin.id)})
        
        # Prepare response
        admin_response = AdminOut(
            id=admin.id,
            username=admin.username,
            email=admin.email,
            phone=admin.phone,
            role=admin.role,
            organization_id=admin.organization_id,
            created_at=admin.created_at
        )
        
        return AdminTokenResponse(
            access_token=access_token,
            token_type="bearer",
            admin=admin_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/admin/profile", response_model=AdminOut)
async def get_admin_profile(
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get current admin profile
    
    Returns the profile of the currently authenticated admin.
    
    Returns:
        - Admin profile details
    """
    try:
        return current_admin
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/admin/profile", response_model=AdminOut)
async def update_admin_profile(
    admin_update: AdminUpdate,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update admin profile
    
    Allows admin to update their profile information.
    
    Returns:
        - Updated admin profile details
    """
    try:
        # Update admin profile
        updated_admin = update_admin(db, str(current_admin.id), **admin_update.dict(exclude_unset=True))
        
        return updated_admin
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/admin/list", response_model=List[AdminOut])
async def list_admins(
    skip: int = 0,
    limit: int = 100,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List all admins (Admin only)
    
    Returns a list of all admin accounts in the system.
    Requires admin authentication.
    
    Returns:
        - List of admin accounts
    """
    try:
        # Check if current admin has permission to list all admins
        if current_admin.role not in ["Owner", "Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list all admins"
            )
        
        admins, total_count = get_all_admins(db, skip, limit)
        
        return admins
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/admin/{admin_id}", response_model=AdminOut)
async def get_admin_by_id_route(
    admin_id: str,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get admin by ID (Admin only)
    
    Returns details of a specific admin account.
    Requires admin authentication.
    
    Returns:
        - Admin account details
    """
    try:
        # Check if current admin has permission
        if current_admin.role not in ["Owner", "Manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view admin details"
            )
        
        admin = get_admin_by_id(db, admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        return admin
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/search-vehicle-owner", response_model=VehicleOwnerInfoResponse, status_code=status.HTTP_200_OK)
async def search_vehicle_owner(
    search_request: SearchVehicleOwnerRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Search Vehicle Owner by Primary Number
    
    Searches for a vehicle owner by their primary phone number.
    Returns vehicle owner information including wallet balance and profile details.
    
    Requires admin authentication.
    
    Returns:
        - Vehicle owner information
        - Wallet balance
        - Profile details
    """
    try:
        vehicle_owner_info = get_vehicle_owner_by_primary_number(db, search_request.primary_number)
        return VehicleOwnerInfoResponse(**vehicle_owner_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/add-money-to-vehicle-owner", response_model=AdminAddMoneyResponse, status_code=status.HTTP_201_CREATED)
async def add_money_to_vehicle_owner(
    vehicle_owner_id: str = Form(..., description="ID of the vehicle owner"),
    transaction_value: int = Form(..., description="Transaction amount in paise (mandatory)"),
    notes: Optional[str] = Form(None, description="Transaction notes"),
    reference_value: Optional[str] = Form(None, description="Optional reference string for the transaction"),
    transaction_img: UploadFile = File(None),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Add Money to Vehicle Owner
    
    Creates a payment transaction to add money to a vehicle owner's wallet.
    
    Requires admin authentication.
    
    Steps:
    1. Validates vehicle owner exists
    2. Uploads transaction image to GCS if provided (optional)
    3. Updates vehicle owner's wallet balance
    4. Creates wallet ledger entry
    5. Records transaction in admin_add_money_to_vehicle_owner table
    
    Returns:
        - Transaction details
        - New wallet balance
        - Transaction ID
    """
    try:
        transaction_img_url = None
        
        # Upload transaction image to GCS if provided
        if transaction_img:
            # Validate file type
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf'}
            file_ext = os.path.splitext(transaction_img.filename)[-1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                )
            
            # Upload to GCS
            transaction_img_url = upload_image_to_gcs(
                transaction_img,
                folder="admin_transactions"
            )
        
        # Create transaction
        result = create_admin_add_money_transaction(
            db=db,
            vehicle_owner_id=vehicle_owner_id,
            transaction_value=transaction_value,
            transaction_img=transaction_img_url,
            notes=notes,
            reference_value=reference_value
        )
        
        return AdminAddMoneyResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============ VENDOR MANAGEMENT ENDPOINTS ============

@router.get("/admin-vendor/vendors", response_model=VendorListOut)
async def list_all_vendors(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List All Vendors (Admin Only)
    
    Returns a paginated list of all vendors in the system with mandatory fields.
    
    Requires admin authentication.
    
    Returns:
        - List of vendors with mandatory fields
        - Total count of vendors
    """
    try:
        vendors, total_count = get_all_vendors(db, skip, limit)
        return VendorListOut(
            vendors=vendors,
            total_count=total_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/admin/vendors/{vendor_id}", response_model=VendorFullDetailsResponse)
async def get_vendor_details(
    vendor_id: UUID,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get Vendor Full Details (Admin Only)
    
    Returns complete vendor information including:
    - All profile details
    - Document status (with signed URLs for document images)
    - Account status
    
    Requires admin authentication.
    
    Returns:
        - Complete vendor details
        - Document information with status
        - Account status
    """
    try:
        result = get_vendor_full_details(db, str(vendor_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        
        vendor_credentials, vendor_details = result
        
        # Prepare documents
        documents = {}
        if vendor_details.aadhar_front_img:
            documents["aadhar"] = {
                "document_type": "aadhar",
                "status": vendor_details.aadhar_status.value if vendor_details.aadhar_status else None,
                "image_url": generate_signed_url_from_gcs(vendor_details.aadhar_front_img) if vendor_details.aadhar_front_img else None
            }
        
        return VendorFullDetailsResponse(
            id=vendor_details.id,
            vendor_id=vendor_details.vendor_id,
            full_name=vendor_details.full_name,
            primary_number=vendor_details.primary_number,
            secondary_number=vendor_details.secondary_number,
            gpay_number=vendor_details.gpay_number,
            wallet_balance=vendor_details.wallet_balance,
            bank_balance=vendor_details.bank_balance,
            aadhar_number=vendor_details.aadhar_number,
            aadhar_front_img=generate_signed_url_from_gcs(vendor_details.aadhar_front_img) if vendor_details.aadhar_front_img else None,
            aadhar_status=vendor_details.aadhar_status.value if vendor_details.aadhar_status else None,
            address=vendor_details.address,
            city=vendor_details.city,
            pincode=vendor_details.pincode,
            account_status=vendor_credentials.account_status.value,
            documents=documents,
            created_at=vendor_details.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/vendors/{vendor_id}/account-status", response_model=StatusUpdateResponse)
async def update_vendor_account_status_route(
    vendor_id: UUID,
    status_update: UpdateAccountStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Vendor Account Status (Admin Only)
    
    Allows admin to change the account status of a vendor.
    Valid statuses: ACTIVE, INACTIVE, PENDING
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Vendor ID
        - New account status
    """
    try:
        updated_vendor = update_vendor_account_status(db, str(vendor_id), status_update.account_status)
        return StatusUpdateResponse(
            message="Vendor account status updated successfully",
            id=updated_vendor.id,
            new_status=updated_vendor.account_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/vendors/{vendor_id}/document-status", response_model=StatusUpdateResponse)
async def update_vendor_document_status_route(
    vendor_id: UUID,
    status_update: UpdateDocumentStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Vendor Document Status (Admin Only)
    
    Allows admin to change the document verification status of a vendor.
    Valid statuses: PENDING, VERIFIED, INVALID
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Vendor ID
        - New document status
    """
    try:
        doc_status = DocumentStatusEnum[status_update.document_status.upper()]
        updated_vendor = update_vendor_document_status(db, str(vendor_id), doc_status)
        return StatusUpdateResponse(
            message="Vendor document status updated successfully",
            id=updated_vendor.id,
            new_status=updated_vendor.aadhar_status.value
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document status. Must be one of: PENDING, VERIFIED, INVALID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============ VEHICLE OWNER MANAGEMENT ENDPOINTS ============

@router.get("/admin-vehcile-owner/vehicle-owners", response_model=VehicleOwnerListOut)
async def list_all_vehicle_owners(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    List All Vehicle Owners (Admin Only)
    
    Returns a paginated list of all vehicle owners in the system with mandatory fields.
    
    Requires admin authentication.
    
    Returns:
        - List of vehicle owners with mandatory fields
        - Total count of vehicle owners
    """
    try:
        vehicle_owners, total_count = get_all_vehicle_owners(db, skip, limit)
        return VehicleOwnerListOut(
            vehicle_owners=vehicle_owners,
            total_count=total_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/admin/vehicle-owners/{vehicle_owner_id}", response_model=VehicleOwnerWithAssetsResponse)
async def get_vehicle_owner_details(
    vehicle_owner_id: UUID,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get Vehicle Owner Full Details with Cars and Drivers (Admin Only)
    
    Returns complete vehicle owner information including:
    - All profile details
    - Document status (with signed URLs for document images)
    - Account status
    - List of all cars owned by the vehicle owner
    - List of all drivers associated with the vehicle owner
    
    Requires admin authentication.
    
    Returns:
        - Complete vehicle owner details
        - Document information with status
        - Account status
        - List of cars with their details and statuses
        - List of drivers with their details and statuses
    """
    try:
        result = get_vehicle_owner_full_details(db, str(vehicle_owner_id))
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle owner not found"
            )
        
        vehicle_owner_credentials, vehicle_owner_details = result
        
        # Prepare documents
        documents = {}
        if vehicle_owner_details.aadhar_front_img:
            documents["aadhar"] = {
                "document_type": "aadhar",
                "status": vehicle_owner_details.aadhar_status.value if vehicle_owner_details.aadhar_status else None,
                "image_url": generate_signed_url_from_gcs(vehicle_owner_details.aadhar_front_img) if vehicle_owner_details.aadhar_front_img else None
            }
        
        # Get vehicle owner details
        owner_details = VehicleOwnerFullDetailsResponse(
            id=vehicle_owner_details.id,
            vehicle_owner_id=vehicle_owner_details.vehicle_owner_id,
            full_name=vehicle_owner_details.full_name,
            primary_number=vehicle_owner_details.primary_number,
            secondary_number=vehicle_owner_details.secondary_number,
            wallet_balance=vehicle_owner_details.wallet_balance,
            aadhar_number=vehicle_owner_details.aadhar_number,
            aadhar_front_img=generate_signed_url_from_gcs(vehicle_owner_details.aadhar_front_img) if vehicle_owner_details.aadhar_front_img else None,
            aadhar_status=vehicle_owner_details.aadhar_status.value if vehicle_owner_details.aadhar_status else None,
            address=vehicle_owner_details.address,
            city=vehicle_owner_details.city,
            pincode=vehicle_owner_details.pincode,
            account_status=vehicle_owner_credentials.account_status.value,
            documents=documents,
            created_at=vehicle_owner_details.created_at
        )
        
        # Get cars
        cars = get_vehicle_owner_cars(db, str(vehicle_owner_id))
        cars_list = []
        for car in cars:
            cars_list.append({
                "id": car.id,
                "vehicle_owner_id": car.vehicle_owner_id,
                "car_name": car.car_name,
                "car_type": car.car_type.value,
                "car_number": car.car_number,
                "year_of_the_car": car.year_of_the_car,
                "rc_front_img_url": generate_signed_url_from_gcs(car.rc_front_img_url) if car.rc_front_img_url else None,
                "rc_front_status": car.rc_front_status.value if car.rc_front_status else None,
                "rc_back_img_url": generate_signed_url_from_gcs(car.rc_back_img_url) if car.rc_back_img_url else None,
                "rc_back_status": car.rc_back_status.value if car.rc_back_status else None,
                "insurance_img_url": generate_signed_url_from_gcs(car.insurance_img_url) if car.insurance_img_url else None,
                "insurance_status": car.insurance_status.value if car.insurance_status else None,
                "fc_img_url": generate_signed_url_from_gcs(car.fc_img_url) if car.fc_img_url else None,
                "fc_status": car.fc_status.value if car.fc_status else None,
                "car_img_url": generate_signed_url_from_gcs(car.car_img_url) if car.car_img_url else None,
                "car_img_status": car.car_img_status.value if car.car_img_status else None,
                "car_status": car.car_status.value,
                "created_at": car.created_at
            })
        
        # Get drivers
        drivers = get_vehicle_owner_drivers(db, str(vehicle_owner_id))
        drivers_list = []
        for driver in drivers:
            drivers_list.append({
                "id": driver.id,
                "vehicle_owner_id": driver.vehicle_owner_id,
                "full_name": driver.full_name,
                "primary_number": driver.primary_number,
                "secondary_number": driver.secondary_number,
                "licence_number": driver.licence_number,
                "licence_front_img": generate_signed_url_from_gcs(driver.licence_front_img) if driver.licence_front_img else None,
                "licence_front_status": driver.licence_front_status.value if driver.licence_front_status else None,
                "address": driver.address,
                "city": driver.city,
                "pincode": driver.pincode,
                "driver_status": driver.driver_status.value,
                "created_at": driver.created_at
            })
        
        return VehicleOwnerWithAssetsResponse(
            vehicle_owner=owner_details,
            cars=cars_list,
            drivers=drivers_list
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/vehicle-owners/{vehicle_owner_id}/account-status", response_model=StatusUpdateResponse)
async def update_vehicle_owner_account_status_route(
    vehicle_owner_id: UUID,
    status_update: UpdateAccountStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Vehicle Owner Account Status (Admin Only)
    
    Allows admin to change the account status of a vehicle owner.
    Valid statuses: ACTIVE, INACTIVE, PENDING
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Vehicle owner ID
        - New account status
    """
    try:
        updated_owner = update_vehicle_owner_account_status(db, str(vehicle_owner_id), status_update.account_status)
        return StatusUpdateResponse(
            message="Vehicle owner account status updated successfully",
            id=updated_owner.id,
            new_status=updated_owner.account_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/vehicle-owners/{vehicle_owner_id}/document-status", response_model=StatusUpdateResponse)
async def update_vehicle_owner_document_status_route(
    vehicle_owner_id: UUID,
    status_update: UpdateDocumentStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Vehicle Owner Document Status (Admin Only)
    
    Allows admin to change the document verification status of a vehicle owner.
    Valid statuses: PENDING, VERIFIED, INVALID
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Vehicle owner ID
        - New document status
    """
    try:
        doc_status = DocumentStatusEnum[status_update.document_status.upper()]
        updated_owner = update_vehicle_owner_document_status(db, str(vehicle_owner_id), doc_status)
        return StatusUpdateResponse(
            message="Vehicle owner document status updated successfully",
            id=updated_owner.id,
            new_status=updated_owner.aadhar_status.value
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document status. Must be one of: PENDING, VERIFIED, INVALID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============ CAR MANAGEMENT ENDPOINTS ============

@router.patch("/admin/cars/{car_id}/account-status", response_model=StatusUpdateResponse)
async def update_car_account_status_route(
    car_id: UUID,
    status_update: UpdateAccountStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Car Account Status (Admin Only)
    
    Allows admin to change the status of a car.
    Valid statuses: ONLINE, DRIVING, BLOCKED, PROCESSING
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Car ID
        - New car status
    """
    try:
        updated_car = update_car_account_status(db, str(car_id), status_update.account_status)
        return StatusUpdateResponse(
            message="Car status updated successfully",
            id=updated_car.id,
            new_status=updated_car.car_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/cars/{car_id}/document-status", response_model=StatusUpdateResponse)
async def update_car_document_status_route(
    car_id: UUID,
    document_type: str = Query(..., description="Document type: rc_front, rc_back, insurance, fc, car_img"),
    status_update: UpdateDocumentStatusRequest = ...,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Car Document Status (Admin Only)
    
    Allows admin to change the document verification status of a car document.
    Valid document types: rc_front, rc_back, insurance, fc, car_img
    Valid statuses: PENDING, VERIFIED, INVALID
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Car ID
        - New document status
    """
    try:
        doc_status = DocumentStatusEnum[status_update.document_status.upper()]
        updated_car = update_car_document_status(db, str(car_id), document_type, doc_status)
        
        # Get the status field value
        status_field_map = {
            "rc_front": updated_car.rc_front_status.value if updated_car.rc_front_status else None,
            "rc_back": updated_car.rc_back_status.value if updated_car.rc_back_status else None,
            "insurance": updated_car.insurance_status.value if updated_car.insurance_status else None,
            "fc": updated_car.fc_status.value if updated_car.fc_status else None,
            "car_img": updated_car.car_img_status.value if updated_car.car_img_status else None,
        }
        
        return StatusUpdateResponse(
            message=f"Car {document_type} document status updated successfully",
            id=updated_car.id,
            new_status=status_field_map.get(document_type, doc_status.value)
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document status. Must be one of: PENDING, VERIFIED, INVALID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============ DRIVER MANAGEMENT ENDPOINTS ============

@router.patch("/admin/drivers/{driver_id}/account-status", response_model=StatusUpdateResponse)
async def update_driver_account_status_route(
    driver_id: UUID,
    status_update: UpdateAccountStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Driver Account Status (Admin Only)
    
    Allows admin to change the status of a driver.
    Valid statuses: ONLINE, OFFLINE, DRIVING, BLOCKED, PROCESSING
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Driver ID
        - New driver status
    """
    try:
        updated_driver = update_driver_account_status(db, str(driver_id), status_update.account_status)
        return StatusUpdateResponse(
            message="Driver status updated successfully",
            id=updated_driver.id,
            new_status=updated_driver.driver_status.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/drivers/{driver_id}/document-status", response_model=StatusUpdateResponse)
async def update_driver_document_status_route(
    driver_id: UUID,
    status_update: UpdateDocumentStatusRequest,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Driver Document Status (Admin Only)
    
    Allows admin to change the document verification status of a driver's license.
    Valid statuses: PENDING, VERIFIED, INVALID
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Driver ID
        - New document status
    """
    try:
        doc_status = DocumentStatusEnum[status_update.document_status.upper()]
        updated_driver = update_driver_document_status(db, str(driver_id), doc_status)
        return StatusUpdateResponse(
            message="Driver document status updated successfully",
            id=updated_driver.id,
            new_status=updated_driver.licence_front_status.value
        )
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document status. Must be one of: PENDING, VERIFIED, INVALID"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
