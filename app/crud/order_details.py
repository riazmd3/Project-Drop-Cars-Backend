from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from app.models.orders import Order
from app.models.order_assignments import OrderAssignment
from app.models.end_records import EndRecord
from app.models.vendor import VendorCredentials
from app.models.vendor_details import VendorDetails
from app.models.car_driver import CarDriver
from app.models.car_details import CarDetails
from app.models.vehicle_owner import VehicleOwnerCredentials
from app.models.vehicle_owner_details import VehicleOwnerDetails
from app.schemas.order_details import (
    AdminOrderDetailResponse, 
    VendorOrderDetailResponse,
    VehicleOwnerOrderDetailResponse,
    VendorBasicInfo,
    DriverBasicInfo,
    CarBasicInfo,
    VehicleOwnerBasicInfo,
    OrderAssignmentDetail,
    EndRecordDetail
)


def get_order_by_id(db: Session, order_id: int) -> Optional[Order]:
    """Get order by ID"""
    return db.query(Order).filter(Order.id == order_id).first()


def get_vendor_basic_info(db: Session, vendor_id: str) -> Optional[VendorBasicInfo]:
    """Get basic vendor information"""
    vendor_creds = db.query(VendorCredentials).filter(VendorCredentials.id == vendor_id).first()
    if not vendor_creds:
        return None
    
    vendor_details = db.query(VendorDetails).filter(VendorDetails.vendor_id == vendor_id).first()
    if not vendor_details:
        return None
    
    return VendorBasicInfo(
        id=vendor_creds.id,
        full_name=vendor_details.full_name,
        primary_number=vendor_details.primary_number,
        secondary_number=vendor_details.secondary_number,
        gpay_number=vendor_details.gpay_number,
        aadhar_number=vendor_details.aadhar_number,
        address=vendor_details.adress,
        wallet_balance=vendor_details.wallet_balance,
        bank_balance=vendor_details.bank_balance,
        created_at=vendor_creds.created_at
    )


def get_driver_basic_info(db: Session, driver_id: str) -> Optional[DriverBasicInfo]:
    """Get basic driver information"""
    driver = db.query(CarDriver).filter(CarDriver.id == driver_id).first()
    if not driver:
        return None
    
    return DriverBasicInfo(
        id=driver.id,
        full_name=driver.full_name,
        primary_number=driver.primary_number,
        secondary_number=driver.secondary_number,
        licence_number=driver.licence_number,
        address=driver.adress,
        driver_status=driver.driver_status.value,
        created_at=driver.created_at
    )


def get_car_basic_info(db: Session, car_id: str) -> Optional[CarBasicInfo]:
    """Get basic car information"""
    car = db.query(CarDetails).filter(CarDetails.id == car_id).first()
    if not car:
        return None
    
    return CarBasicInfo(
        id=car.id,
        car_name=car.car_name,
        car_type=car.car_type.value,
        car_number=car.car_number,
        car_status=car.car_status.value,
        rc_front_img_url=car.rc_front_img_url,
        rc_back_img_url=car.rc_back_img_url,
        insurance_img_url=car.insurance_img_url,
        fc_img_url=car.fc_img_url,
        car_img_url=car.car_img_url,
        created_at=car.created_at
    )


def get_vehicle_owner_basic_info(db: Session, vehicle_owner_id: str) -> Optional[VehicleOwnerBasicInfo]:
    """Get basic vehicle owner information"""
    owner_creds = db.query(VehicleOwnerCredentials).filter(VehicleOwnerCredentials.id == vehicle_owner_id).first()
    if not owner_creds:
        return None
    
    owner_details = db.query(VehicleOwnerDetails).filter(VehicleOwnerDetails.vehicle_owner_id == vehicle_owner_id).first()
    if not owner_details:
        return None
    
    return VehicleOwnerBasicInfo(
        id=owner_creds.id,
        full_name=owner_details.full_name,
        primary_number=owner_details.primary_number,
        secondary_number=owner_details.secondary_number,
        address=owner_details.adress,
        account_status=owner_creds.account_status.value,
        created_at=owner_creds.created_at
    )


def get_order_assignments(db: Session, order_id: int) -> list[OrderAssignmentDetail]:
    """Get all order assignments for an order"""
    assignments = db.query(OrderAssignment).filter(OrderAssignment.order_id == order_id).all()
    
    return [
        OrderAssignmentDetail(
            id=assignment.id,
            order_id=assignment.order_id,
            vehicle_owner_id=assignment.vehicle_owner_id,
            driver_id=assignment.driver_id,
            car_id=assignment.car_id,
            assignment_status=assignment.assignment_status,
            assigned_at=assignment.assigned_at,
            expires_at=assignment.expires_at,
            cancelled_at=assignment.cancelled_at,
            completed_at=assignment.completed_at,
            created_at=assignment.created_at
        )
        for assignment in assignments
    ]


def get_order_end_records(db: Session, order_id: int) -> list[EndRecordDetail]:
    """Get all end records for an order"""
    end_records = db.query(EndRecord).filter(EndRecord.order_id == order_id).all()
    
    return [
        EndRecordDetail(
            id=record.id,
            order_id=record.order_id,
            driver_id=record.driver_id,
            start_km=record.start_km,
            end_km=record.end_km,
            contact_number=record.contact_number,
            img_url=record.img_url,
            close_speedometer_image=record.close_speedometer_image,
            created_at=record.created_at,
            updated_at=record.updated_at
        )
        for record in end_records
    ]


def get_admin_order_details(db: Session, order_id: int) -> Optional[AdminOrderDetailResponse]:
    """Get full order details for admin with all related data"""
    order = get_order_by_id(db, order_id)
    if not order:
        return None
    
    # Get vendor information
    vendor = get_vendor_basic_info(db, str(order.vendor_id))
    if not vendor:
        return None
    
    # Get assignments
    assignments = get_order_assignments(db, order_id)
    
    # Get end records
    end_records = get_order_end_records(db, order_id)
    
    # Get latest assignment details
    latest_assignment = None
    assigned_driver = None
    assigned_car = None
    vehicle_owner = None
    
    if assignments:
        latest_assignment = assignments[-1]  # Most recent assignment
        
        if latest_assignment.driver_id:
            assigned_driver = get_driver_basic_info(db, str(latest_assignment.driver_id))
        
        if latest_assignment.car_id:
            assigned_car = get_car_basic_info(db, str(latest_assignment.car_id))
        
        if latest_assignment.vehicle_owner_id:
            vehicle_owner = get_vehicle_owner_basic_info(db, str(latest_assignment.vehicle_owner_id))
    
    return AdminOrderDetailResponse(
        id=order.id,
        source=order.source.value,
        source_order_id=order.source_order_id,
        vendor_id=order.vendor_id,
        trip_type=order.trip_type.value,
        car_type=order.car_type.value,
        pickup_drop_location=order.pickup_drop_location,
        start_date_time=order.start_date_time,
        customer_name=order.customer_name,
        customer_number=order.customer_number,
        trip_status=order.trip_status,
        pick_near_city=order.pick_near_city,
        trip_distance=order.trip_distance,
        trip_time=order.trip_time,
        estimated_price=order.estimated_price,
        vendor_price=order.vendor_price,
        platform_fees_percent=order.platform_fees_percent,
        closed_vendor_price=order.closed_vendor_price,
        closed_driver_price=order.closed_driver_price,
        commision_amount=order.commision_amount,
        created_at=order.created_at,
        vendor=vendor,
        assignments=assignments,
        end_records=end_records,
        assigned_driver=assigned_driver,
        assigned_car=assigned_car,
        vehicle_owner=vehicle_owner
    )


def get_vendor_order_details(db: Session, order_id: int, vendor_id: str) -> Optional[VendorOrderDetailResponse]:
    """Get limited order details for vendor (excludes sensitive user data)"""
    order = get_order_by_id(db, order_id)
    if not order:
        return None
    
    # Check if vendor owns this order
    if str(order.vendor_id) != vendor_id:
        return None
    
    # Get assignments
    assignments = get_order_assignments(db, order_id)
    
    # Get end records
    end_records = get_order_end_records(db, order_id)
    
    # Get limited info from latest assignment
    assigned_driver_name = None
    assigned_driver_phone = None
    assigned_car_name = None
    assigned_car_number = None
    vehicle_owner_name = None
    
    if assignments:
        latest_assignment = assignments[-1]  # Most recent assignment
        
        if latest_assignment.driver_id:
            driver = db.query(CarDriver).filter(CarDriver.id == latest_assignment.driver_id).first()
            if driver:
                assigned_driver_name = driver.full_name
                assigned_driver_phone = driver.primary_number
        
        if latest_assignment.car_id:
            car = db.query(CarDetails).filter(CarDetails.id == latest_assignment.car_id).first()
            if car:
                assigned_car_name = car.car_name
                assigned_car_number = car.car_number
        
        if latest_assignment.vehicle_owner_id:
            owner_details = db.query(VehicleOwnerDetails).filter(
                VehicleOwnerDetails.vehicle_owner_id == latest_assignment.vehicle_owner_id
            ).first()
            if owner_details:
                vehicle_owner_name = owner_details.full_name
    
    return VendorOrderDetailResponse(
        id=order.id,
        source=order.source.value,
        source_order_id=order.source_order_id,
        vendor_id=order.vendor_id,
        trip_type=order.trip_type.value,
        car_type=order.car_type.value,
        pickup_drop_location=order.pickup_drop_location,
        start_date_time=order.start_date_time,
        customer_name=order.customer_name,
        customer_number=order.customer_number,
        trip_status=order.trip_status,
        pick_near_city=order.pick_near_city,
        trip_distance=order.trip_distance,
        trip_time=order.trip_time,
        estimated_price=order.estimated_price,
        vendor_price=order.vendor_price,
        platform_fees_percent=order.platform_fees_percent,
        closed_vendor_price=order.closed_vendor_price,
        closed_driver_price=order.closed_driver_price,
        commision_amount=order.commision_amount,
        created_at=order.created_at,
        assignments=assignments,
        end_records=end_records,
        assigned_driver_name=assigned_driver_name,
        assigned_driver_phone=assigned_driver_phone,
        assigned_car_name=assigned_car_name,
        assigned_car_number=assigned_car_number,
        vehicle_owner_name=vehicle_owner_name
    )


def get_vehicle_owner_orders_by_assignment_status(
    db: Session, 
    vehicle_owner_id: str, 
    assignment_status: str
) -> List[VehicleOwnerOrderDetailResponse]:
    """Get orders for vehicle owner filtered by assignment status"""
    from sqlalchemy import and_, or_
    
    # Query to join orders with order_assignments and filter by vehicle_owner_id and assignment_status
    query = db.query(Order, OrderAssignment).join(
        OrderAssignment, Order.id == OrderAssignment.order_id
    ).filter(
        and_(
            OrderAssignment.vehicle_owner_id == vehicle_owner_id,
            or_(
                OrderAssignment.assignment_status == assignment_status,
                OrderAssignment.assignment_status == "ASSIGNED"
            )
        )
    ).order_by(Order.created_at.desc())
    
    results = []
    
    for order, assignment in query.all():
        # Get basic vendor info
        vendor_name = None
        vendor_phone = None
        vendor_details = db.query(VendorDetails).filter(VendorDetails.vendor_id == str(order.vendor_id)).first()
        if vendor_details:
            vendor_name = vendor_details.full_name
            vendor_phone = vendor_details.primary_number
        
        # Get driver and car info if assigned
        assigned_driver_name = None
        assigned_driver_phone = None
        assigned_car_name = None
        assigned_car_number = None
        
        if assignment.driver_id:
            driver = db.query(CarDriver).filter(CarDriver.id == assignment.driver_id).first()
            if driver:
                assigned_driver_name = driver.full_name
                assigned_driver_phone = driver.primary_number
        
        if assignment.car_id:
            car = db.query(CarDetails).filter(CarDetails.id == assignment.car_id).first()
            if car:
                assigned_car_name = car.car_name
                assigned_car_number = car.car_number
        
        result = VehicleOwnerOrderDetailResponse(
            # Order information
            id=order.id,
            source=order.source.value,
            source_order_id=order.source_order_id,
            vendor_id=order.vendor_id,
            trip_type=order.trip_type.value,
            car_type=order.car_type.value,
            pickup_drop_location=order.pickup_drop_location,
            start_date_time=order.start_date_time,
            customer_name=order.customer_name,
            customer_number=order.customer_number,
            trip_status=order.trip_status,
            pick_near_city=order.pick_near_city,
            trip_distance=order.trip_distance,
            trip_time=order.trip_time,
            estimated_price=order.estimated_price,
            vendor_price=order.vendor_price,
            platform_fees_percent=order.platform_fees_percent,
            closed_vendor_price=order.closed_vendor_price,
            closed_driver_price=order.closed_driver_price,
            commision_amount=order.commision_amount,
            created_at=order.created_at,
            
            # Assignment information
            assignment_id=assignment.id,
            assignment_status=assignment.assignment_status,
            assigned_at=assignment.assigned_at,
            expires_at=assignment.expires_at,
            cancelled_at=assignment.cancelled_at,
            completed_at=assignment.completed_at,
            assignment_created_at=assignment.created_at,
            
            # Vendor info
            vendor_name=vendor_name,
            vendor_phone=vendor_phone,
            
            # Driver and car info
            assigned_driver_name=assigned_driver_name,
            assigned_driver_phone=assigned_driver_phone,
            assigned_car_name=assigned_car_name,
            assigned_car_number=assigned_car_number
        )
        
        results.append(result)
    
    return results


def get_vehicle_owner_pending_orders(db: Session, vehicle_owner_id: str) -> List[VehicleOwnerOrderDetailResponse]:
    """Get pending orders for vehicle owner"""
    return get_vehicle_owner_orders_by_assignment_status(db, vehicle_owner_id, "PENDING")


def get_vehicle_owner_non_pending_orders(db: Session, vehicle_owner_id: str) -> List[VehicleOwnerOrderDetailResponse]:
    """Get non-pending orders for vehicle owner (ASSIGNED, CANCELLED, COMPLETED, DRIVING)"""
    from sqlalchemy import and_, not_
    print("vehicle_owner_id", vehicle_owner_id)
    # Query to join orders with order_assignments and filter by vehicle_owner_id and non-pending status
    query = db.query(Order, OrderAssignment).join(
        OrderAssignment, Order.id == OrderAssignment.order_id
    ).filter(
        and_(
            OrderAssignment.vehicle_owner_id == vehicle_owner_id,
            OrderAssignment.assignment_status != "PENDING",
            OrderAssignment.assignment_status != "ASSIGNED"
        )
    ).order_by(Order.created_at.desc())
    
    results = []
    
    for order, assignment in query.all():
        # Get basic vendor info
        vendor_name = None
        vendor_phone = None
        vendor_details = db.query(VendorDetails).filter(VendorDetails.vendor_id == str(order.vendor_id)).first()
        if vendor_details:
            vendor_name = vendor_details.full_name
            vendor_phone = vendor_details.primary_number
        
        # Get driver and car info if assigned
        assigned_driver_name = None
        assigned_driver_phone = None
        assigned_car_name = None
        assigned_car_number = None
        
        if assignment.driver_id:
            driver = db.query(CarDriver).filter(CarDriver.id == assignment.driver_id).first()
            if driver:
                assigned_driver_name = driver.full_name
                assigned_driver_phone = driver.primary_number
        
        if assignment.car_id:
            car = db.query(CarDetails).filter(CarDetails.id == assignment.car_id).first()
            if car:
                assigned_car_name = car.car_name
                assigned_car_number = car.car_number
        
        result = VehicleOwnerOrderDetailResponse(
            # Order information
            id=order.id,
            source=order.source.value,
            source_order_id=order.source_order_id,
            vendor_id=order.vendor_id,
            trip_type=order.trip_type.value,
            car_type=order.car_type.value,
            pickup_drop_location=order.pickup_drop_location,
            start_date_time=order.start_date_time,
            customer_name=order.customer_name,
            customer_number=order.customer_number,
            trip_status=order.trip_status,
            pick_near_city=order.pick_near_city,
            trip_distance=order.trip_distance,
            trip_time=order.trip_time,
            estimated_price=order.estimated_price,
            vendor_price=order.vendor_price,
            platform_fees_percent=order.platform_fees_percent,
            closed_vendor_price=order.closed_vendor_price,
            closed_driver_price=order.closed_driver_price,
            commision_amount=order.commision_amount,
            created_at=order.created_at,
            
            # Assignment information
            assignment_id=assignment.id,
            assignment_status=assignment.assignment_status,
            assigned_at=assignment.assigned_at,
            expires_at=assignment.expires_at,
            cancelled_at=assignment.cancelled_at,
            completed_at=assignment.completed_at,
            assignment_created_at=assignment.created_at,
            
            # Vendor info
            vendor_name=vendor_name,
            vendor_phone=vendor_phone,
            
            # Driver and car info
            assigned_driver_name=assigned_driver_name,
            assigned_driver_phone=assigned_driver_phone,
            assigned_car_name=assigned_car_name,
            assigned_car_number=assigned_car_number
        )
        
        results.append(result)
    
    return results
