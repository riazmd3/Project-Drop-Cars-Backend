# models/vendor.py
from sqlalchemy import Column, String, TIMESTAMP, Integer, func, Boolean, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base

class AccountStatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    
class VendorCredentials(Base):
    __tablename__ = "vendor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    # organization_id = Column(String)
    primary_number = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    account_status = Column(
        SqlEnum(AccountStatusEnum, name="account_status_enum"),
        default=AccountStatusEnum.INACTIVE,
        nullable=False
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
