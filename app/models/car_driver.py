# models/car_driver.py
from sqlalchemy import Column, String, Integer, TIMESTAMP, func, Boolean, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base
import uuid
import enum
from app.models.common_enums import DocumentStatusEnum
class AccountStatusEnum(enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DRIVING = "DRIVING"
    BLOCKED = "BLOCKED"
    PROCESSING = "PROCESSING"


class CarDriver(Base):
    __tablename__ = "car_driver"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vehicle_owner_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_owner.id"), nullable=False)
    full_name = Column(String, nullable=False)
    primary_number = Column(String, nullable=False, unique=True)
    secondary_number = Column(String, nullable=True, unique=True)
    hashed_password = Column(String, nullable=False)
    licence_number = Column(String, nullable=False, unique=True)
    licence_front_img = Column(String, nullable=True, unique=True)
    licence_front_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    driver_status = Column(
        SqlEnum(AccountStatusEnum, name="driver_status_enum"),
        default=AccountStatusEnum.OFFLINE,
        nullable=False
    )  # Online, Offline, Driving, Blocked, Processing
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
