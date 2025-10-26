# models/vehicle_owner.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Boolean, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base

class AccountStatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    
class VehicleOwnerCredentials(Base):
    __tablename__ = "vehicle_owner"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    primary_number = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    account_status = Column(
        SqlEnum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.INACTIVE,
        nullable=False
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    driver_profile = Column(Integer, nullable=False, default=0)
    car_profile = Column(Integer, nullable=False, default=0)
    
