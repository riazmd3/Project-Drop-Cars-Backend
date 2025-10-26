# models/vendor_details.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Boolean, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base
from app.models.common_enums import DocumentStatusEnum

class VendorDetails(Base):
    __tablename__ = "vendor_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor.id"), nullable=False)
    full_name = Column(String, nullable=False)
    primary_number = Column(String, unique=True, nullable=False)
    secondary_number = Column(String, unique=True, nullable=True)
    wallet_balance = Column(Integer, nullable=False, default=0)
    bank_balance = Column(Integer, nullable=False, default=0)
    gpay_number = Column(String, unique=True, nullable=False)
    aadhar_number = Column(String, unique=True, nullable=False)
    aadhar_front_img = Column(String, unique=True, nullable=True)
    aadhar_status = Column(SqlEnum(DocumentStatusEnum, name="document_status_enum"), nullable=True, default=DocumentStatusEnum.PENDING)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
