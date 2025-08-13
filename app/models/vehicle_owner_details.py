# models/vehicle_owner.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Boolean, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base

class VehicleOwnerDetails(Base):
    __tablename__ = "vehicle_owner_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vehicle_owner_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_owner.id"), nullable=False)
    organization_id = Column(String)
    full_name = Column(String, nullable=False)
    primary_number = Column(String, unique=True, nullable=False)
    secondary_number = Column(String, unique=True, nullable=True)
    wallet_balance = Column(Integer, nullable=False, default=0)
    gpay_number = Column(String, unique=True, nullable=False)
    aadhar_number = Column(String, unique=True, nullable=False)
    aadhar_front_img = Column(String, unique=True, nullable=True)
    adress = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    # owner_profile_status = Column(Boolean, nullable=False, default=False)
    # driver_profile = Column(Boolean, nullable=False, default=False)
    # car_profile = Column(Boolean, nullable=False, default=False)
    
