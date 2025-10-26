# app/models/admin.py
from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database.session import Base

class Admin(Base):
    __tablename__ = "admin"
    
    # id = Column(Integer, primary_key=True, index=True)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String)
    password = Column(String)
    role = Column(String)  # Owner, Manager
    email = Column(String)
    phone = Column(String(10), nullable=False)
    # organization_id = Column(String)
    organization_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    
    # Admin balance tracking
    balance = Column(Integer, nullable=False, default=0)
    
    # Timestamp In UTC Format
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False
    )
