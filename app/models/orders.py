from sqlalchemy import Column, String, TIMESTAMP, Integer, func, JSON, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.database.session import Base
from app.models.new_orders import OrderTypeEnum, CarTypeEnum


class OrderSourceEnum(str, enum.Enum):
    NEW_ORDERS = "NEW_ORDERS"
    HOURLY_RENTAL = "HOURLY_RENTAL"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(SqlEnum(OrderSourceEnum, name="ORDER_SOURCE_ENUM"), nullable=False)
    source_order_id = Column(Integer, nullable=False)

    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor.id"), nullable=False)
    trip_type = Column(SqlEnum(OrderTypeEnum, name="ORDER_TYPE_ENUM"), nullable=False)
    car_type = Column(SqlEnum(CarTypeEnum, name="CAR_TYPE_ENUM"), nullable=False)
    pickup_drop_location = Column(JSON, nullable=False)
    start_date_time = Column(TIMESTAMP(timezone=True), nullable=False)
    customer_name = Column(String, nullable=False)
    customer_number = Column(String, nullable=False)

    # Optional shared financials/summaries
    trip_status = Column(String, nullable=True)
    pick_near_city = Column(String, nullable=True)
    trip_distance = Column(Integer, nullable=True)
    trip_time = Column(String, nullable=True)
    estimated_price = Column(Integer, nullable=True)
    vendor_price = Column(Integer, nullable=True)
    platform_fees_percent = Column(Integer, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


