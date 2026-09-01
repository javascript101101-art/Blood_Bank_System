from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID

class InventoryBase(BaseModel):
    blood_group: str
    rh_factor: str
    blood_component: str = "Whole_Blood"
    quantity_ml: int
    expiry_date: date
    status: str = "Available"
    
    # 🟢 သွေးအိတ်နံပါတ် (Unit ID) ကို API မှ လက်ခံ/ထုတ်ပေးနိုင်ရန် ထည့်သွင်းခြင်း
    unit_id: Optional[str] = None

class InventoryCreate(InventoryBase):
    hospital_id: Optional[UUID] = None
    donor_id: Optional[UUID] = None
    # 🟢 Traceability အတွက် ထပ်ဖြည့်ရန်
    blood_request_id: Optional[UUID] = None 
    storage_condition: Optional[str] = None

# 🟢 [အသစ်] API မှ Update လုပ်ရာတွင် အသုံးပြုရန်
class InventoryUpdate(BaseModel):
    blood_group: Optional[str] = None
    rh_factor: Optional[str] = None
    blood_component: Optional[str] = None
    quantity_ml: Optional[int] = None
    expiry_date: Optional[date] = None
    status: Optional[str] = None
    unit_id: Optional[str] = None
    hospital_id: Optional[UUID] = None
    donor_id: Optional[UUID] = None
    blood_request_id: Optional[UUID] = None
    storage_condition: Optional[str] = None

class InventoryResponse(InventoryBase):
    id: UUID
    hospital_id: UUID
    donor_id: Optional[UUID] = None
    # 🟢 API မှ ပြန်ထုတ်ပေးသည့်အခါ ပါသွားအောင် ထပ်ဖြည့်ရန်
    blood_request_id: Optional[UUID] = None
    storage_condition: Optional[str] = None

    class Config:
        from_attributes = True