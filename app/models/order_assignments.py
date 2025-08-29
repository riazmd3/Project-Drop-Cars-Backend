# models/new_orders.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, JSON, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base
from datetime import datetime


class AssignmentStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    DRIVING = "DRIVING"


class OrderAssignment(Base):
    __tablename__ = "order_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("new_orders.order_id"), nullable=False)
    vehicle_owner_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_owner.id"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("car_driver.id"), nullable=True)
    car_id = Column(UUID(as_uuid=True), ForeignKey("car_details.id"), nullable=True)

    assignment_status = Column(SqlEnum(AssignmentStatusEnum), nullable=False, default=AssignmentStatusEnum.PENDING)

    assigned_at = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP)
    cancelled_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Optional: define relationships if needed
    # order = relationship("NewOrder")
    # driver = relationship("CarDriver")
    # car = relationship("CarDetail")
    # owner = relationship("VehicleOwner")