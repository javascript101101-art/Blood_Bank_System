from sqlalchemy import Column, String, Integer, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel

class BloodRequest(BaseModel):
    __tablename__ = "blood_requests"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    patient_name = Column(String(255), nullable=False)
    blood_group = Column(String(3), nullable=False)
    rh_factor = Column(String(10), nullable=False)
    quantity_ml = Column(Integer, nullable=False)
    urgency = Column(String(20), default="Normal")
    status = Column(String(20), default="Pending")
    requested_at = Column(DateTime, server_default=func.now())
    fulfilled_at = Column(DateTime)

    hospital = relationship("Hospital", back_populates="requests")
    requester = relationship("User", back_populates="requests")