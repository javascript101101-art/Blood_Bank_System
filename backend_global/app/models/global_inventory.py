from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid
from datetime import datetime

class GlobalInventory(BaseModel):
    __tablename__ = "global_inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 🟢 သွေးအိတ်နံပါတ် (Unit ID)
    unit_id = Column(String(50), nullable=True, index=True)

    blood_component = Column(String(50), nullable=False, default="Whole_Blood")
    blood_group = Column(String(20), nullable=False)
    rh_factor = Column(String(20), nullable=False)
    quantity_ml = Column(Integer, default=0)

    # ==========================================
    # 🟢 [အသစ်] Real World စနစ်အတွက် ထပ်တိုးထားသော ကော်လံများ
    # ==========================================
    supplier = Column(String(255), nullable=True) # ဥပမာ - WHO, Red Cross, Mass Blood Drive
    expiry_date = Column(DateTime, nullable=True) # သက်တမ်းကုန်ဆုံးရက်
    status = Column(String(50), default="Available") # Available, In-Transit, Used, Expired စသဖြင့်

    source_hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True)
    source_request_id = Column(UUID(as_uuid=True), nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_hospital = relationship("Hospital", foreign_keys=[source_hospital_id])

    def __repr__(self):
        # 🟢 Debug တွင် Supplier ကိုပါ မြင်ရအောင် ထည့်ထားပါသည်
        return f"<GlobalInventory {self.unit_id or 'No-ID'} | {self.supplier or 'Local'} | {self.blood_component} {self.blood_group} {self.rh_factor}: {self.quantity_ml}ml>"