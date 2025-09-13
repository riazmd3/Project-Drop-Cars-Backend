# schemas/admin.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- Admin Base Schema ---
class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Admin email address")
    phone: str = Field(..., min_length=10, max_length=10, description="10-digit Indian mobile number (starting with 6-9)")
    role: str = Field(..., description="Admin role (Owner, Manager, etc.)")
    organization_id: Optional[str] = None

# --- Admin Signup Schema ---
class AdminSignup(AdminBase):
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

    @validator('phone')
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError('Phone number must contain only digits')
        if len(v) != 10:
            raise ValueError('Phone number must be exactly 10 digits')
        if not v.startswith(('6', '7', '8', '9')):
            raise ValueError('Phone number must start with 6, 7, 8, or 9 for Indian mobile numbers')
        return v

    @validator('email')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v

# --- Admin Signin Schema ---
class AdminSignin(BaseModel):
    username: str
    password: str

# --- Admin Response Schema ---
class AdminOut(BaseModel):
    id: UUID
    username: str
    email: str
    phone: str
    role: str
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "username": "admin_user",
                "email": "admin@dropcars.com",
                "phone": "9876543210",
                "role": "Manager",
                "organization_id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "created_at": "2025-08-13T12:00:00Z"
            }
        }

# --- Admin Token Response Schema ---
class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    admin: AdminOut

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "admin": {
                    "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
                    "username": "admin_user",
                    "email": "admin@dropcars.com",
                    "phone": "9876543210",
                    "role": "Manager",
                    "organization_id": "org_123",
                    "created_at": "2025-08-13T12:00:00Z"
                }
            }
        }

# --- Admin Update Schema ---
class AdminUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, description="Admin email address")
    phone: Optional[str] = Field(None, min_length=10, max_length=10, description="10-digit Indian mobile number (starting with 6-9)")
    role: Optional[str] = Field(None, description="Admin role")
    organization_id: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            if not v.isdigit():
                raise ValueError('Phone number must contain only digits')
            if len(v) != 10:
                raise ValueError('Phone number must be exactly 10 digits')
            if not v.startswith(('6', '7', '8', '9')):
                raise ValueError('Phone number must start with 6, 7, 8, or 9 for Indian mobile numbers')
        return v

    @validator('email')
    def validate_email(cls, v):
        if v is not None:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, v):
                raise ValueError('Invalid email format')
        return v
