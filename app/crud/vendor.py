# from sqlalchemy.orm import Session
# from fastapi import HTTPException
# from app.models.vendor import User
# from app.schemas.car_driver import UserCreate
# from app.core.security import get_password_hash, verify_password

# def create_user(db: Session, user: UserCreate):
#     existing_user = db.query(User).filter(User.mobile_number == user.mobile_number).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="User Number already registered")

#     hashed_password = get_password_hash(user.password)

#     db_user = User(
#         full_name=user.full_name,
#         mobile_number=user.mobile_number,
#         hashed_password=hashed_password,
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def authenticate_user(db: Session, mobile_number: str, password: str):
#     user = db.query(User).filter(User.mobile_number == mobile_number).first()
#     if not user or not verify_password(password, user.hashed_password):
#         return None
#     return user
