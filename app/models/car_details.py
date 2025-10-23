# models/car_details.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Enum as SqlEnum, ForeignKey
import uuid
import enum
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base
from app.models.common_enums import DocumentStatusEnum

class CarStatusEnum(enum.Enum):
    ONLINE = "ONLINE"
    DRIVING = "DRIVING"
    BLOCKED = "BLOCKED"
    PROCESSING = "PROCESSING"
    
class CarTypeEnum(enum.Enum):
    SEDAN = "SEDAN"
    SUV = "SUV"
    INNOVA = "INNOVA"
    NEW_SEDAN = "NEW_SEDAN"
    HATCHBACK = "HATCHBACK"
    INNOVA_CRYSTA = "INNOVA_CRYSTA"

class CarDetails(Base):
    __tablename__ = "car_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vehicle_owner_id = Column(UUID(as_uuid=True), ForeignKey("vehicle_owner.id"), nullable=False)
    organization_id = Column(String)
    car_name = Column(String, nullable=False)
    car_type = Column(SqlEnum(CarTypeEnum,name="car_type_enum"),nullable=False)  # sedan, suv, muv, innova
    car_number = Column(String, nullable=False, unique=True)
    
    rc_front_img_url = Column(String, nullable=True, unique=True)     # GCS public URL
    rc_front_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    rc_back_img_url = Column(String, nullable=True, unique=True)      # GCS public URL
    rc_back_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    insurance_img_url = Column(String , nullable=True, unique=True)  # GCS public URL
    insurance_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    fc_img_url = Column(String, nullable=True, unique=True)  # GCS public URL
    fc_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    car_img_url = Column(String, nullable=True, unique=True)  # GCS public URL
    car_img_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    
    car_status = Column(
        SqlEnum(CarStatusEnum, name="car_status_enum"),
        default=CarStatusEnum.PROCESSING,
        nullable=False
    ) 
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
