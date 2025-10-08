from sqlalchemy import Column, String, TIMESTAMP, Integer, func, ForeignKey, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from app.database.session import Base


class VendorLedgerEntryType(str, enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class VendorWalletLedger(Base):
    __tablename__ = "vendor_wallet_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendor.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    entry_type = Column(SqlEnum(VendorLedgerEntryType, name="vendor_wallet_entry_type_enum"), nullable=False)
    amount = Column(Integer, nullable=False)
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


