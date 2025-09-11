from sqlalchemy import Column, String, TIMESTAMP, Integer, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.session import Base


class EndRecord(Base):
    __tablename__ = "end_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("car_driver.id"), nullable=False)

    start_km = Column(Integer, nullable=False)
    end_km = Column(Integer, nullable=False)
    contact_number = Column(String, nullable=False)
    img_url = Column(String, nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


