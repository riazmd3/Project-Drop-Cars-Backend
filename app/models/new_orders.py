# models/new_orders.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, JSON, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum
from app.database.session import Base

class OrderTypeEnum(enum.Enum):
    ONEWAY = "Oneway"
    ROUND_TRIP = "Round Trip"
    HOURLY_RENTAL = "Hourly Rental"
    MULTY_CITY = "Multy City"

class CarTypeEnum(enum.Enum):
    HATCHBACK = "Hatchback"
    SEDAN = "Sedan"
    NEW_SEDAN = "New Sedan"
    SUV = "SUV"
    INNOVA = "Innova"
    INNOVA_CRYSTA = "Innova Crysta"


class NewOrder(Base):
    __tablename__ = "new_orders"

    order_id  = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor.id"), nullable=False)
    trip_type = Column(
        SqlEnum(OrderTypeEnum, name="ORDER_TYPE_ENUM"),
        nullable=False
    )
    car_type = Column(
        SqlEnum(CarTypeEnum, name="CAR_TYPE_ENUM"),
        nullable=False
    )
    pickup_drop_location = Column(JSON, nullable=False)
    start_date_time = Column(TIMESTAMP(timezone=True), nullable=False)
    customer_name = Column(String, nullable=False)
    customer_number = Column(String, nullable=False)
    cost_per_km = Column(Integer, nullable=False)
    extra_cost_per_km = Column(Integer, nullable=False)
    driver_allowance = Column(Integer, nullable=False)
    extra_driver_allowance = Column(Integer, nullable=False)
    permit_charges = Column(Integer, nullable=False)
    extra_permit_charges = Column(Integer, nullable=False)
    hill_charges = Column(Integer, nullable=False)
    toll_charges = Column(Integer, nullable=False)
    pickup_notes = Column(String, nullable=True)
    trip_status = Column(String, nullable=False)
    pick_near_city = Column(ARRAY(String), nullable=False)
    trip_distance = Column(Integer,nullable=False)
    trip_time = Column(String, nullable=False)
    platform_fees_percent = Column(Integer,nullable=False)
    estimated_price = Column(Integer, nullable=True)
    vendor_price  = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    
