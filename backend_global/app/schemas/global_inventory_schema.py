from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class GlobalInventoryBase(BaseModel):
    blood_component: str # 🟢 သွေးအစိတ်အပိုင်း အသစ်ထည့်သွင်းထားပါသည်
    blood_group: str
    rh_factor: str
    quantity_ml: int

class GlobalInventoryCreate(GlobalInventoryBase):
    source_hospital_id: Optional[UUID] = None
    source_request_id: Optional[UUID] = None

class GlobalInventoryResponse(GlobalInventoryBase):
    id: UUID
    source_hospital_id: Optional[UUID]
    source_request_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GlobalInventorySummary(BaseModel):
    """Blood type နှင့် Component အလိုက် စုစုပေါင်း"""
    blood_component: str # 🟢 Summary တွင် Component ပါဝင်ရန် ထည့်သွင်းထားပါသည်
    blood_group: str
    rh_factor: str
    total_ml: int


class DeliverBloodRequest(BaseModel):
    """Global Inventory ကနေ Hospital ဆီ Blood ပို့ရန်"""
    blood_component: str # 🟢 ပို့ဆောင်ရာတွင်လည်း Component ကို ခွဲခြားရန် ထည့်သွင်းထားပါသည်
    blood_group: str
    rh_factor: str
    quantity_ml: int = Field(..., gt=0)
    destination_hospital_id: UUID
    global_request_id: Optional[UUID] = None