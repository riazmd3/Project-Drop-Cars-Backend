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
    update_car_account_status, update_car_document_status, update_driver_account_status, update_driver_document_status,
    get_all_accounts_unified, get_account_details_by_id,
    get_all_account_documents, update_document_status_by_id, update_unified_account_status,
    get_all_cars_unified
)
from app.schemas.admin_management import (
    VendorListOut, VendorFullDetailsResponse, VehicleOwnerListOut, VehicleOwnerFullDetailsResponse,
    UpdateAccountStatusRequest, UpdateDocumentStatusRequest, StatusUpdateResponse,
    CarListResponse, DriverListResponse, VehicleOwnerWithAssetsResponse,
    AccountListResponse, AccountListItem, AccountFullDetailsResponse,
    AccountDocumentsResponse, DocumentItem, DocumentStatusUpdateResponse,
    CarListItem
)
from app.schemas.order_details import AdminOrdersListResponse
from app.crud.order_details import get_all_admin_orders
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

# ============ UNIFIED ACCOUNT MANAGEMENT ENDPOINTS ============
# NOTE: These routes must come BEFORE /admin/{admin_id} to avoid route conflicts

@router.get("/admin/orders", response_model=AdminOrdersListResponse)
async def list_all_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get All Orders (Admin Only)
    
    Returns a paginated list of all orders in the system with complete details including:
    - Order information (id, source, trip type, car type, customer details, pricing, etc.)
    - Vendor information (full vendor details)
    - Assignment history (all assignments for the order)
    - End records (trip completion records)
    - Driver information (if assigned)
    - Car information (if assigned)
    - Vehicle owner information (if assigned)
    
    Requires admin authentication.
    
    Returns:
        - List of orders with full details
        - Total count of orders
        - Pagination info (skip, limit)
    """
    try:
        orders, total_count = get_all_admin_orders(db, skip=skip, limit=limit)
        
        return AdminOrdersListResponse(
            orders=orders,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/admin/cars", response_model=CarListResponse)
async def list_all_cars(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    vehicle_owner_id: Optional[str] = Query(None, description="Filter by vehicle owner ID"),
    status_filter: Optional[str] = Query(None, description="Filter by car status: ONLINE, DRIVING, BLOCKED, PROCESSING"),
    car_type_filter: Optional[str] = Query(None, description="Filter by car type"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get All Cars (Admin Only)
    
    Returns a list of all cars in the system with basic information:
    - ID
    - Car Name
    - Car Type
    - Car Number
    - Car Status (ONLINE, DRIVING, BLOCKED, PROCESSING)
    - Vehicle Owner ID and Name
    - Year of the Car
    
    Supports filtering by:
    - vehicle_owner_id: Filter by specific vehicle owner
    - status_filter: Filter by car status
    - car_type_filter: Filter by car type
    
    Requires admin authentication.
    
    Returns:
        - List of cars with basic info
        - Total count
        - Status counts (online, blocked, processing, driving)
    """
    try:
        cars, total_count, online_count, blocked_count, processing_count, driving_count = get_all_cars_unified(
            db=db,
            skip=skip,
            limit=limit,
            vehicle_owner_id=vehicle_owner_id,
            status_filter=status_filter,
            car_type_filter=car_type_filter
        )
        
        car_items = [
            CarListItem(
                id=car["id"],
                vehicle_owner_id=car["vehicle_owner_id"],
                car_name=car["car_name"],
                car_type=car["car_type"],
                car_number=car["car_number"],
                year_of_the_car=car["year_of_the_car"],
                car_status=car["car_status"],
                vehicle_owner_name=car["vehicle_owner_name"],
                created_at=car["created_at"]
            )
            for car in cars
        ]
        
        return CarListResponse(
            cars=car_items,
            total_count=total_count,
            online_count=online_count,
            blocked_count=blocked_count,
            processing_count=processing_count,
            driving_count=driving_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/admin/accounts", response_model=AccountListResponse)
async def list_all_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    account_type: Optional[str] = Query(None, description="Filter by account type: vendor, vehicle_owner, driver, quickdriver"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, pending, ONLINE, OFFLINE, etc."),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get All Accounts (Admin Only)
    
    Returns a unified list of all accounts (vendors, vehicle owners, drivers) with basic information:
    - ID
    - Name
    - Account Type (vendor, vehicle_owner, driver)
    - Account Status (Active, Inactive, Pending, ONLINE, OFFLINE, etc.)
    
    Supports filtering by:
    - account_type: Filter by specific account type
    - status_filter: Filter by status (active, inactive, pending, or specific statuses)
    
    Requires admin authentication.
    
    Returns:
        - List of accounts with basic info
        - Total count
        - Active count
        - Inactive count
    """
    try:
        accounts, total_count, active_count, inactive_count = get_all_accounts_unified(
            db=db,
            skip=skip,
            limit=limit,
            account_type=account_type,
            status_filter=status_filter
        )
        
        account_items = [
            AccountListItem(
                id=acc["id"],
                name=acc["name"],
                account_type=acc["account_type"],
                account_status=acc["account_status"]
            )
            for acc in accounts
        ]
        
        return AccountListResponse(
            accounts=account_items,
            total_count=total_count,
            active_count=active_count,
            inactive_count=inactive_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/admin/accounts/{account_id}", response_model=AccountFullDetailsResponse)
async def get_account_details(
    account_id: UUID,
    account_type: str = Query(..., description="Account type: vendor, vehicle_owner, driver, or quickdriver"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get Account Full Details by ID (Admin Only)
    
    Returns complete details of a specific account based on ID and account type.
    
    Account types supported:
    - vendor: Returns vendor full details
    - vehicle_owner: Returns vehicle owner full details
    - driver or quickdriver: Returns driver full details
    
    Requires admin authentication.
    
    Returns:
        - Complete account details including all profile information
        - Document status
        - Account status
    """
    try:
        account_details = get_account_details_by_id(db, str(account_id), account_type)
        
        if not account_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found with ID {account_id} and type {account_type}"
            )
        
        # Prepare documents if available
        documents = None
        if account_details.get("aadhar_front_img"):
            from app.schemas.admin_management import VendorDocumentInfo
            documents = {
                "aadhar": VendorDocumentInfo(
                    document_type="aadhar",
                    status=account_details.get("aadhar_status"),
                    image_url=generate_signed_url_from_gcs(account_details.get("aadhar_front_img")) if account_details.get("aadhar_front_img") else None
                )
            }
        elif account_details.get("licence_front_img"):
            from app.schemas.admin_management import VendorDocumentInfo
            documents = {
                "licence": VendorDocumentInfo(
                    document_type="licence",
                    status=account_details.get("licence_front_status"),
                    image_url=generate_signed_url_from_gcs(account_details.get("licence_front_img")) if account_details.get("licence_front_img") else None
                )
            }
        
        # Generate signed URLs for images if they exist
        aadhar_img_url = None
        if account_details.get("aadhar_front_img"):
            aadhar_img_url = generate_signed_url_from_gcs(account_details.get("aadhar_front_img"))
        
        licence_img_url = None
        if account_details.get("licence_front_img"):
            licence_img_url = generate_signed_url_from_gcs(account_details.get("licence_front_img"))
        
        return AccountFullDetailsResponse(
            id=account_details["id"],
            account_type=account_details["account_type"],
            account_status=account_details["account_status"],
            vendor_id=account_details.get("vendor_id"),
            vehicle_owner_id=account_details.get("vehicle_owner_id"),
            full_name=account_details.get("full_name"),
            primary_number=account_details.get("primary_number"),
            secondary_number=account_details.get("secondary_number"),
            gpay_number=account_details.get("gpay_number"),
            wallet_balance=account_details.get("wallet_balance"),
            bank_balance=account_details.get("bank_balance"),
            aadhar_number=account_details.get("aadhar_number"),
            aadhar_front_img=aadhar_img_url,
            aadhar_status=account_details.get("aadhar_status"),
            address=account_details.get("address"),
            city=account_details.get("city"),
            pincode=account_details.get("pincode"),
            licence_number=account_details.get("licence_number"),
            licence_front_img=licence_img_url,
            licence_front_status=account_details.get("licence_front_status"),
            created_at=account_details.get("created_at"),
            documents=documents
        )
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

# ============ DOCUMENT VERIFICATION ENDPOINTS ============

@router.get("/admin/accounts/{account_id}/documents", response_model=AccountDocumentsResponse)
async def get_account_documents(
    account_id: UUID,
    account_type: str = Query(..., description="Account type: vendor, vehicle_owner, driver, or quickdriver"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get All Documents for an Account (Admin Only)
    
    Returns all documents uploaded by an account:
    - Account documents (Aadhar for vendors/vehicle owners, License for drivers)
    - Car documents (if vehicle owner: RC front/back, Insurance, FC, Car Image, Permit)
    
    Each document includes:
    - Document ID (for updating status)
    - Document type and name
    - Image URL (signed URL)
    - Current status (PENDING, VERIFIED, INVALID)
    - Upload date
    - Car information (for car documents)
    
    Requires admin authentication.
    
    Returns:
        - All account documents
        - All car documents (if vehicle owner)
        - Document counts (total, pending, verified, invalid)
    """
    try:
        documents_data = get_all_account_documents(db, str(account_id), account_type)
        
        if not documents_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account not found with ID {account_id} and type {account_type}"
            )
        
        # Convert to DocumentItem objects
        account_docs = [
            DocumentItem(**doc) for doc in documents_data["account_documents"]
        ]
        car_docs = [
            DocumentItem(**doc) for doc in documents_data["car_documents"]
        ]
        
        return AccountDocumentsResponse(
            account_id=UUID(documents_data["account_id"]),
            account_type=documents_data["account_type"],
            account_name=documents_data["account_name"],
            account_documents=account_docs,
            car_documents=car_docs,
            total_documents=documents_data["total_documents"],
            pending_count=documents_data["pending_count"],
            verified_count=documents_data["verified_count"],
            invalid_count=documents_data["invalid_count"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.patch("/admin/accounts/{account_id}/documents/{document_id}/status", response_model=DocumentStatusUpdateResponse)
async def update_document_status(
    account_id: UUID,
    document_id: str,
    account_type: str = Query(..., description="Account type: vendor, vehicle_owner, driver, or quickdriver"),
    status: str = Query(..., description="New status: PENDING, VERIFIED, or INVALID"),
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Document Status (Admin Only)
    
    Updates the verification status of a specific document.
    
    Document ID formats:
    - Account documents: "account_aadhar", "account_licence"
    - Car documents: "car_{car_id}_{doc_type}" (e.g., "car_123_rc_front")
    
    Valid statuses:
    - PENDING: Document is pending verification
    - VERIFIED: Document is verified and accepted
    - INVALID: Document is invalid/rejected
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Document ID
        - Document type
        - New status
    """
    try:
        result = update_document_status_by_id(
            db=db,
            account_id=str(account_id),
            account_type=account_type,
            document_id=document_id,
            new_status=status
        )
        
        return DocumentStatusUpdateResponse(
            message=result["message"],
            document_id=result["document_id"],
            document_type=result["document_type"],
            new_status=result["new_status"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# ============ UNIFIED ACCOUNT STATUS UPDATE ============

@router.patch("/admin/accounts/{account_id}/status", response_model=StatusUpdateResponse)
async def update_account_status_unified(
    account_id: UUID,
    account_type: str = Query(..., description="Account type: vendor, vehicle_owner, driver, or quickdriver"),
    status_param: Optional[str] = Query(None, alias="status", description="New status (can also be sent in body)"),
    status_update: Optional[UpdateAccountStatusRequest] = None,
    current_admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update Account Status (Admin Only) - Unified Endpoint
    
    Updates the account status for any account type (vendor, vehicle owner, or driver).
    
    You can send the status either as:
    - Query parameter: ?status=Active
    - Request body: { "account_status": "Active" }
    
    Valid statuses for Vendors & Vehicle Owners:
    - Active: Account is active and can use the system
    - Inactive: Account is inactive and cannot use the system
    - Pending: Account is pending approval
    
    Valid statuses for Drivers:
    - ONLINE: Driver is online and available
    - OFFLINE: Driver is offline
    - DRIVING: Driver is currently on a trip
    - BLOCKED: Driver is blocked
    - PROCESSING: Driver account is being processed
    
    Requires admin authentication.
    
    Returns:
        - Success message
        - Account ID
        - New account status
    """
    try:
        # Get status from query parameter or request body
        if status_param:
            new_status = status_param
        elif status_update and status_update.account_status:
            new_status = status_update.account_status
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required. Provide it either as query parameter 'status' or in request body as 'account_status'"
            )
        
        result = update_unified_account_status(
            db=db,
            account_id=str(account_id),
            account_type=account_type,
            new_status=new_status
        )
        
        # Convert id to UUID if it's a string, otherwise use as-is (it might already be a UUID)
        result_id = result["id"]
        if isinstance(result_id, UUID):
            # Already a UUID, use it directly
            pass
        elif isinstance(result_id, str):
            result_id = UUID(result_id)
        else:
            result_id = UUID(str(result_id))
        
        return StatusUpdateResponse(
            message=result["message"],
            id=result_id,
            new_status=result["new_status"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

