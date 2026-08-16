from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Inventory(BaseModel):
    __tablename__ = "inventory"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    
    # 🟢 အသစ်ထပ်တိုးထားသော ကော်လံများ (Local နှင့် ကိုက်ညီစေရန်)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id", ondelete="SET NULL"), nullable=True)
    
    # 🟢 ဤနေရာတွင် Traceability အတွက် blood_request_id ထပ်ထည့်ရပါမည်
    blood_request_id = Column(UUID(as_uuid=True), nullable=True)
    
    blood_group = Column(String(3), nullable=False)
    rh_factor = Column(String(10), nullable=False)
    
    # 🟢 သွေးအစိတ်အပိုင်းနှင့် သိမ်းဆည်းမည့် အပူချိန်
    blood_component = Column(String(50), nullable=False, default="Whole_Blood")
    storage_condition = Column(String(100))
    
    quantity_ml = Column(Integer, nullable=False, default=0)
    expiry_date = Column(Date, nullable=False)
    status = Column(String(20), default="Available")

    hospital = relationship("Hospital", back_populates="inventories")
    # donor_id နှင့် ချိတ်ဆက်ရန် relationship ထည့်ပေးထားပါသည်
    donor = relationship("Donor")