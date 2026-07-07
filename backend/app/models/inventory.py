from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Inventory(BaseModel):
    __tablename__ = "inventory"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    blood_group = Column(String(3), nullable=False)
    rh_factor = Column(String(10), nullable=False)
    quantity_ml = Column(Integer, nullable=False, default=0)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(20), default="Available")

    hospital = relationship("Hospital", back_populates="inventories")