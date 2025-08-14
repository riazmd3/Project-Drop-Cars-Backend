# models/car_driver.py
from sqlalchemy import Column, String, Integer, TIMESTAMP, func, Boolean, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base
import uuid
import enum
class AccountStatusEnum(enum.Enum):
    ONLINE = "ONLINE"
    DRIVING = "DRIVING"
    BLOCKED = "BLOCKED"

class CarDriver(Base):
    __tablename__ = "car_driver"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    organization_id = Column(String)
    full_name = Column(String, nullable=False)
    primary_number = Column(String, nullable=False, unique=True)
    secondary_number = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    licence_number = Column(String, nullable=False, unique=True)
    licence_front_img = Column(String, nullable=True, unique=True)
    adress = Column(String, nullable=False)
    driver_status = Column(
        SqlEnum(AccountStatusEnum, name="driver_status_enum"),
        default=AccountStatusEnum.BLOCKED,
        nullable=False
    )  # Online, Driving, Blocked
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
