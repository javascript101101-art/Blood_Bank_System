from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from sqlalchemy.sql import func

class GlobalBloodRequest(BaseModel):
    __tablename__ = "global_blood_requests"

    requesting_hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    
    # 🟢 String(3) မှ String(50) သို့ ပြောင်းထားပါသည် (Error မတက်စေရန်)
    blood_group = Column(String(50), nullable=False)
    rh_factor = Column(String(10), nullable=False)
    
    # 🆕 အခုမှ အသစ်ထပ်ထည့်လိုက်သော Component ကော်လံ
    blood_component = Column(String(50), default="Whole_Blood")
    
    quantity_ml = Column(Integer, nullable=False)
    urgency = Column(String(20), default="Normal")
    status = Column(String(20), default="Pending")
    assigned_hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    request_note = Column(Text)
    
    # Relationships
    requesting_hospital = relationship("Hospital", foreign_keys=[requesting_hospital_id])
    assigned_hospital = relationship("Hospital", foreign_keys=[assigned_hospital_id])