# crud/admin.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.admin import Admin
from typing import Optional
import uuid

def get_admin_by_id(db: Session, admin_id: str):
    """Get admin by ID"""
    return db.query(Admin).filter(
        Admin.id == admin_id
    ).first()

def get_admin_by_username(db: Session, username: str):
    """Get admin by username"""
    return db.query(Admin).filter(
        Admin.username == username
    ).first()

def get_admin_by_phone(db: Session, phone: str):
    """Get admin by phone number"""
    return db.query(Admin).filter(
        Admin.phone == phone
    ).first()

def get_admin_by_email(db: Session, email: str):
    """Get admin by email address"""
    return db.query(Admin).filter(
        Admin.email == email
    ).first()

def create_admin(db: Session, username: str, hashed_password: str, role: str, email: str, phone: str):
    """Create a new admin"""
    admin = Admin(
        username=username,
        password=hashed_password,
        role=role,
        email=email,
        phone=phone
    )
    
    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin: {str(e)}"
        )

def authenticate_admin(db: Session, username: str, password: str):
    """Authenticate admin with username and password"""
    from app.core.security import verify_password
    
    admin = get_admin_by_username(db, username)
    
    if not admin or not verify_password(password, admin.password):
        return None
    
    return admin

def get_all_admins(db: Session, skip: int = 0, limit: int = 100):
    """Get all admins with pagination"""
    admins = db.query(Admin).offset(skip).limit(limit).all()
    total_count = db.query(Admin).count()
    return admins, total_count

def update_admin(db: Session, admin_id: str, **kwargs):
    """Update admin details"""
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    try:
        for key, value in kwargs.items():
            if hasattr(admin, key):
                setattr(admin, key, value)
        
        db.commit()
        db.refresh(admin)
        return admin
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin: {str(e)}"
        )

def delete_admin(db: Session, admin_id: str):
    """Delete admin"""
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    try:
        db.delete(admin)
        db.commit()
        return {"message": "Admin deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete admin: {str(e)}"
        )
