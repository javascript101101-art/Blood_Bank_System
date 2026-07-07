from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Donor(BaseModel):
    __tablename__ = "donors"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    dob = Column(Date)
    blood_group = Column(String(3), nullable=False)
    rh_factor = Column(String(10), nullable=False)
    contact_phone = Column(String(20))
    email = Column(String(255))
    last_donation_date = Column(Date)

    hospital = relationship("Hospital", back_populates="donors")