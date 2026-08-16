from sqlalchemy import Column, String, Text, Boolean, ForeignKey 
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=True) # Global Admin အတွက် NULL ခွင့်ပြု
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False) # Global_Admin, Hospital_Admin, Lab_Staff, Receptionist
    is_active = Column(Boolean, default=True)

    hospital = relationship("Hospital", back_populates="users")
    # 🟢 ဤလိုင်းကို ဖယ်ရှားပါ (သို့မဟုတ် # ဖြင့် မှတ်ထားပါ)
    # requests = relationship("BloodRequest", back_populates="requester")