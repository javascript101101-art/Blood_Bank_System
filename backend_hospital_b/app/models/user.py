from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 🆕 Self-Registration အတွက်
    is_approved = Column(Boolean, default=False)  # Admin က Approve လုပ်မှသာ Login ဝင်လို့ရမယ်

    # Relationships
    hospital = relationship("Hospital", back_populates="users")
    requests = relationship("BloodRequest", back_populates="requester")
    
    # 🟢 Clinic Profile နှင့် One-to-One ချိတ်ဆက်ခြင်း (နည်းလမ်း ၂ အတွက် မပါမဖြစ်)
    clinic_profile = relationship("ClinicProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")