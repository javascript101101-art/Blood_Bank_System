from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class ClinicProfile(BaseModel):
    __tablename__ = "clinic_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    clinic_name = Column(String(255), nullable=False)
    license = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    contact_email = Column(String(100), nullable=False)
    clinic_address = Column(Text, nullable=False)

    # 🟢 User နှင့် ပြန်လည်ချိတ်ဆက်ခြင်း
    user = relationship("User", back_populates="clinic_profile")