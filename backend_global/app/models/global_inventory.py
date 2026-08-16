from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid
from datetime import datetime

class GlobalInventory(BaseModel):
    __tablename__ = "global_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blood_component = Column(String(50), nullable=False, default="Whole_Blood") # 🟢 သွေးအစိတ်အပိုင်းအတွက် ကော်လံအသစ်
    blood_group = Column(String(20), nullable=False) # 🟢 String(3) မှ (20) သို့ ပြောင်းထားပါသည် (Error မတက်စေရန်)
    rh_factor = Column(String(20), nullable=False)
    quantity_ml = Column(Integer, default=0)
    source_hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    source_request_id = Column(UUID(as_uuid=True), nullable=True)  # ဘယ် Request ကနေ လာတယ်ဆိုတာ
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_hospital = relationship("Hospital", foreign_keys=[source_hospital_id])

    def __repr__(self):
        return f"<GlobalInventory {self.blood_component} {self.blood_group} {self.rh_factor}: {self.quantity_ml}ml>"