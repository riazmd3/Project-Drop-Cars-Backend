# crud/admin_management.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from app.models.vendor import VendorCredentials, AccountStatusEnum as VendorAccountStatusEnum
from app.models.vendor_details import VendorDetails
from app.models.vehicle_owner import VehicleOwnerCredentials, AccountStatusEnum as VehicleOwnerAccountStatusEnum
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.models.car_details import CarDetails, CarStatusEnum
from app.models.car_driver import CarDriver, AccountStatusEnum as DriverStatusEnum
from app.models.common_enums import DocumentStatusEnum
from typing import List, Optional, Tuple
from uuid import UUID

# ============ VENDOR MANAGEMENT ============

def get_all_vendors(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[VendorDetails], int]:
    """Get all vendors with pagination"""
    vendors = db.query(VendorDetails).offset(skip).limit(limit).all()
    total_count = db.query(VendorDetails).count()
    return vendors, total_count

def get_vendor_full_details(db: Session, vendor_id: str) -> Optional[Tuple[VendorCredentials, VendorDetails]]:
    """Get full vendor details including credentials and details"""
    vendor_credentials = db.query(VendorCredentials).filter(
        VendorCredentials.id == vendor_id
    ).first()
    
    if not vendor_credentials:
        return None
    
    vendor_details = db.query(VendorDetails).filter(
        VendorDetails.vendor_id == vendor_id
    ).first()
    
    return vendor_credentials, vendor_details

def update_vendor_account_status(db: Session, vendor_id: str, account_status: str) -> VendorCredentials:
    """Update vendor account status"""
    vendor = db.query(VendorCredentials).filter(
        VendorCredentials.id == vendor_id
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Try to match by enum name first (ACTIVE, INACTIVE, PENDING)
    account_status_upper = account_status.upper()
    try:
        vendor.account_status = VendorAccountStatusEnum[account_status_upper]
    except KeyError:
        # Try to match by value (Active, Inactive, Pending)
        for enum_item in VendorAccountStatusEnum:
            if enum_item.value.lower() == account_status.lower():
                vendor.account_status = enum_item
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid account status. Must be one of: {[e.name for e in VendorAccountStatusEnum]} or {[e.value for e in VendorAccountStatusEnum]}"
            )
    
    try:
        db.commit()
        db.refresh(vendor)
        return vendor
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vendor account status: {str(e)}"
        )

def update_vendor_document_status(db: Session, vendor_id: str, document_status: DocumentStatusEnum) -> VendorDetails:
    """Update vendor document status"""
    vendor_details = db.query(VendorDetails).filter(
        VendorDetails.vendor_id == vendor_id
    ).first()
    
    if not vendor_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor details not found"
        )
    
    try:
        vendor_details.aadhar_status = document_status
        db.commit()
        db.refresh(vendor_details)
        return vendor_details
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vendor document status: {str(e)}"
        )

# ============ VEHICLE OWNER MANAGEMENT ============

def get_all_vehicle_owners(db: Session, skip: int = 0, limit: int = 100) -> Tuple[List[VehicleOwnerDetails], int]:
    """Get all vehicle owners with pagination"""
    vehicle_owners = db.query(VehicleOwnerDetails).offset(skip).limit(limit).all()
    total_count = db.query(VehicleOwnerDetails).count()
    return vehicle_owners, total_count

def get_vehicle_owner_full_details(db: Session, vehicle_owner_id: str) -> Optional[Tuple[VehicleOwnerCredentials, VehicleOwnerDetails]]:
    """Get full vehicle owner details including credentials and details"""
    vehicle_owner_credentials = db.query(VehicleOwnerCredentials).filter(
        VehicleOwnerCredentials.id == vehicle_owner_id
    ).first()
    
    if not vehicle_owner_credentials:
        return None
    
    vehicle_owner_details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()
    
    return vehicle_owner_credentials, vehicle_owner_details

def update_vehicle_owner_account_status(db: Session, vehicle_owner_id: str, account_status: str) -> VehicleOwnerCredentials:
    """Update vehicle owner account status"""
    vehicle_owner = db.query(VehicleOwnerCredentials).filter(
        VehicleOwnerCredentials.id == vehicle_owner_id
    ).first()
    
    if not vehicle_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner not found"
        )
    
    # Try to match by enum name first (ACTIVE, INACTIVE, PENDING)
    account_status_upper = account_status.upper()
    try:
        vehicle_owner.account_status = VehicleOwnerAccountStatusEnum[account_status_upper]
    except KeyError:
        # Try to match by value (Active, Inactive, Pending)
        for enum_item in VehicleOwnerAccountStatusEnum:
            if enum_item.value.lower() == account_status.lower():
                vehicle_owner.account_status = enum_item
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid account status. Must be one of: {[e.name for e in VehicleOwnerAccountStatusEnum]} or {[e.value for e in VehicleOwnerAccountStatusEnum]}"
            )
    
    try:
        db.commit()
        db.refresh(vehicle_owner)
        return vehicle_owner
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vehicle owner account status: {str(e)}"
        )

def update_vehicle_owner_document_status(db: Session, vehicle_owner_id: str, document_status: DocumentStatusEnum) -> VehicleOwnerDetails:
    """Update vehicle owner document status"""
    vehicle_owner_details = db.query(VehicleOwnerDetails).filter(
        VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id
    ).first()
    
    if not vehicle_owner_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle owner details not found"
        )
    
    try:
        vehicle_owner_details.aadhar_status = document_status
        db.commit()
        db.refresh(vehicle_owner_details)
        return vehicle_owner_details
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vehicle owner document status: {str(e)}"
        )

def get_vehicle_owner_cars(db: Session, vehicle_owner_id: str) -> List[CarDetails]:
    """Get all cars for a vehicle owner"""
    return db.query(CarDetails).filter(
        CarDetails.vehicle_owner_id == vehicle_owner_id
    ).all()

def get_vehicle_owner_drivers(db: Session, vehicle_owner_id: str) -> List[CarDriver]:
    """Get all drivers for a vehicle owner"""
    return db.query(CarDriver).filter(
        CarDriver.vehicle_owner_id == vehicle_owner_id
    ).all()

# ============ CAR MANAGEMENT ============

def update_car_account_status(db: Session, car_id: str, car_status: str) -> CarDetails:
    """Update car account status"""
    car = db.query(CarDetails).filter(
        CarDetails.id == car_id
    ).first()
    
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    try:
        car.car_status = CarStatusEnum[car_status.upper()]
        db.commit()
        db.refresh(car)
        return car
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid car status. Must be one of: {[e.name for e in CarStatusEnum]}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update car status: {str(e)}"
        )

def update_car_document_status(
    db: Session, 
    car_id: str, 
    document_type: str, 
    document_status: DocumentStatusEnum
) -> CarDetails:
    """Update car document status"""
    car = db.query(CarDetails).filter(
        CarDetails.id == car_id
    ).first()
    
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found"
        )
    
    document_mapping = {
        "rc_front": ("rc_front_status",),
        "rc_back": ("rc_back_status",),
        "insurance": ("insurance_status",),
        "fc": ("fc_status",),
        "car_img": ("car_img_status",),
    }
    
    if document_type not in document_mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {list(document_mapping.keys())}"
        )
    
    try:
        status_field = document_mapping[document_type][0]
        setattr(car, status_field, document_status)
        db.commit()
        db.refresh(car)
        return car
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update car document status: {str(e)}"
        )

# ============ DRIVER MANAGEMENT ============

def update_driver_account_status(db: Session, driver_id: str, driver_status: str) -> CarDriver:
    """Update driver account status"""
    driver = db.query(CarDriver).filter(
        CarDriver.id == driver_id
    ).first()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    try:
        driver.driver_status = DriverStatusEnum[driver_status.upper()]
        db.commit()
        db.refresh(driver)
        return driver
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid driver status. Must be one of: {[e.name for e in DriverStatusEnum]}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update driver status: {str(e)}"
        )

def update_driver_document_status(db: Session, driver_id: str, document_status: DocumentStatusEnum) -> CarDriver:
    """Update driver document status"""
    driver = db.query(CarDriver).filter(
        CarDriver.id == driver_id
    ).first()
    
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    try:
        driver.licence_front_status = document_status
        db.commit()
        db.refresh(driver)
        return driver
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update driver document status: {str(e)}"
        )
