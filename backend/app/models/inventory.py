from sqlalchemy import Column, String, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class Inventory(BaseModel):
    __tablename__ = "inventory"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)

    # 🆕 ဘယ်အလှူရှင် (Donor) ဆီက လာသလဲဆိုတာ ခြေရာခံရန် (Foreign Key)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("donors.id", ondelete="SET NULL"), nullable=True)

    # 🟢 အသစ်ထည့်သွင်းထားသောအပိုင်း - ဘယ် Request အတွက် သုံးလိုက်လဲဆိုတာ ခြေရာခံရန် (Vein-to-Vein Traceability)
    blood_request_id = Column(UUID(as_uuid=True), nullable=True)

    # 🟢 သွေးအိတ်နံပါတ် (Unit ID) - Traceability အတွက် အဓိက အရေးကြီးဆုံးအပိုင်း
    unit_id = Column(String(50), unique=True, index=True, nullable=True)

    blood_group = Column(String(3), nullable=False)
    rh_factor = Column(String(10), nullable=False)

    # 🆕 သွေးအစိတ်အပိုင်း အမျိုးအစား (ဥပမာ - Red_Cells, Plasma, Platelets)
    blood_component = Column(String(50), nullable=False, default="Red_Cells")

    quantity_ml = Column(Integer, nullable=False, default=0)

    # 🆕 သိမ်းဆည်းရမည့် အပူချိန် သတ်မှတ်ချက်
    storage_condition = Column(String(100), nullable=True)

    expiry_date = Column(Date, nullable=False)
    status = Column(String(20), default="Available") # Available, Expired, Discarded, Used, Quarantined

    hospital = relationship("Hospital", back_populates="inventories")
    donor = relationship("Donor", backref="inventories")