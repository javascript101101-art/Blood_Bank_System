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

class InventoryCreate(InventoryBase):
    hospital_id: Optional[UUID] = None
    donor_id: Optional[UUID] = None
    # 🟢 Traceability အတွက် ထပ်ဖြည့်ရန်
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