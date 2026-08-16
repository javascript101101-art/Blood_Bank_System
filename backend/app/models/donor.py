from sqlalchemy import Column, String, Date, Integer, Float, ForeignKey
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
    
    # 🩸 သွေးလှူဒါန်းမှုနှင့် ကျန်းမာရေး စစ်ဆေးချက် အချက်အလက်များ
    last_donation_date = Column(Date, nullable=True)
    donation_quantity = Column(Integer, nullable=False)  # မူလ ၄၅၀ မီလီလီတာ စသည်ဖြင့် ထည့်ရန်
    hemoglobin_level = Column(Float, nullable=True)      # Haemoglobin စစ်ဆေးချက်
    temperature = Column(Float, nullable=True)           # ကိုယ်အပူချိန်
    blood_pressure = Column(String(20), nullable=True)   # သွေးပေါင်ချိန်

    hospital = relationship("Hospital", back_populates="donors")