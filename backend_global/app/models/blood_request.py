from sqlalchemy import Column, String, Integer, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel

class BloodRequest(BaseModel):
    __tablename__ = "blood_requests"

    # Foreign Keys
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    
    # 🟢 ဤနေရာတွင် ForeignKey("users.id") ကို ဖြုတ်လိုက်ပါပြီ (Global တွင် ထို User မရှိနိုင်သောကြောင့်ဖြစ်သည်)
    requested_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 🏥 CLINIC / HOSPITAL INFORMATION
    clinic_name = Column(String(255), nullable=False)
    license = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(100), nullable=False)
    clinic_address = Column(Text, nullable=False)

    # 🩸 BLOOD REQUEST DETAILS
    blood_component = Column(String(50), default="Whole_Blood", nullable=False) 
    blood_group = Column(String(20), nullable=False) 
    quantity_units = Column(Integer, nullable=False) 
    urgency = Column(String(50), default="Normal Request")
    required_date = Column(Date, nullable=False)
    patient_condition = Column(Text, nullable=True)

    # 📊 Tracking
    status = Column(String(20), default="Pending")
    requested_at = Column(DateTime, server_default=func.now())
    fulfilled_at = Column(DateTime)

    # Relationships
    hospital = relationship("Hospital", back_populates="requests")
    # 🟢 ForeignKey မရှိတော့သဖြင့် requester relationship ကို ဖျက်/ပိတ် ထားရပါမည်
    # requester = relationship("User", back_populates="requests")