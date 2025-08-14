# models/car_details.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Enum as SqlEnum
import uuid
import enum
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base

class CarStatusEnum(enum.Enum):
    ONLINE = "ONLINE"
    DRIVING = "DRIVING"
    BLOCKED = "BLOCKED"
    
class CarTypeEnum(enum.Enum):
    SEDAN = "SEDAN"
    SUV = "SUV"
    INNOVA = "INNOVA"

class CarDetails(Base):
    __tablename__ = "car_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    organization_id = Column(String)
    car_name = Column(String, nullable=False)
    car_type = Column(SqlEnum(CarTypeEnum,name="car_type_enum"),nullable=False)  # sedan, suv, muv, innova
    car_number = Column(String, nullable=False, unique=True)
    
    rc_front_img_url = Column(String, nullable=True, unique=True)     # GCS public URL
    rc_back_img_url = Column(String, nullable=True, unique=True)      # GCS public URL
    insurance_img_url = Column(String , nullable=True, unique=True)  # GCS public URL
    fc_img_url = Column(String, nullable=True, unique=True)  # GCS public URL
    car_img_url = Column(String, nullable=True, unique=True)  # GCS public URL
    
    car_status = Column(
        SqlEnum(CarStatusEnum, name="car_status_enum"),
        default=CarStatusEnum.BLOCKED,
        nullable=False
    ) 
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
