from sqlalchemy import Column, String, Boolean
from app.database.session import Base

class Notification(Base):
    __tablename__ = "notifications"
    user = Column(String,nullable=False)
    sub = Column(String, primary_key=True, index=True)  # User ID from JWT
    permission1 = Column(Boolean, default=False)
    permission2 = Column(Boolean, default=False)
    token = Column(String, nullable=True)  # Expo push token
