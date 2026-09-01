from sqlalchemy import Column, String, Integer, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.models.base import BaseModel

class BloodRequest(BaseModel):
    __tablename__ = "blood_requests"

    # Foreign Keys
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    requested_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 🏥 CLINIC / HOSPITAL INFORMATION (Form အသစ်အတွက်)
    clinic_name = Column(String(255), nullable=False)
    license = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(100), nullable=False)
    clinic_address = Column(Text, nullable=False)

    # 🩸 BLOOD REQUEST DETAILS (Form အသစ်အတွက်)
    blood_component = Column(String(50), default="Whole_Blood", nullable=False) 
    blood_group = Column(String(20), nullable=False) 
    quantity_units = Column(Integer, nullable=False) 
    
    # 🟢 [အရေးကြီး ပြင်ဆင်ချက်] ဤနေရာတွင် volume_per_unit_ml မပါလျှင် Error တက်ပါမည်
    volume_per_unit_ml = Column(Integer, nullable=False, default=500) 
    
    urgency = Column(String(50), default="Normal Request")
    required_date = Column(Date, nullable=False)
    patient_condition = Column(Text, nullable=True) 

    # 📊 Tracking
    status = Column(String(20), default="Pending")
    requested_at = Column(DateTime, server_default=func.now())
    fulfilled_at = Column(DateTime)
    
    # 🟢 [အသစ်] ထုတ်ပေးလိုက်သော Unit ID များကို မှတ်သားရန်
    fulfilled_unit_ids = Column(String(500), nullable=True)

    # Relationships
    hospital = relationship("Hospital", back_populates="requests")
    requester = relationship("User", back_populates="requests")
    
    # 🟢 Traceability အတွက် အသစ်ထပ်တိုးခြင်း
    fulfilled_inventories = relationship(
        "Inventory", 
        primaryjoin="BloodRequest.id == foreign(Inventory.blood_request_id)",
        viewonly=True 
    )