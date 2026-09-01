from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List

class GlobalInventoryBase(BaseModel):
    unit_id: Optional[str] = None 
    blood_component: str 
    blood_group: str
    rh_factor: str
    quantity_ml: int # တစ်အိတ်ပါဝင်မည့် ပမာဏ
    
    # ==========================================
    # 🟢 [အသစ်] Real World Data များ
    # ==========================================
    supplier: Optional[str] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = "Available"

class GlobalInventoryCreate(GlobalInventoryBase):
    source_hospital_id: Optional[UUID] = None
    source_request_id: Optional[UUID] = None
    
    # 🟢 [အသစ်] သွေးအိတ် ဘယ်နှအိတ်သွင်းမလဲ (Bulk Insert အတွက်)
    # Default အနေဖြင့် (၁) အိတ်ဟု သတ်မှတ်ထားမည်
    number_of_units: int = Field(default=1, gt=0)

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
    blood_component: str 
    blood_group: str
    rh_factor: str
    total_ml: int

class DeliverBloodRequest(BaseModel):
    """Global Inventory ကနေ Hospital ဆီ Blood ပို့ရန်"""
    unit_id: Optional[str] = None 
    blood_component: str 
    blood_group: str
    rh_factor: str
    quantity_ml: int = Field(..., gt=0)
    destination_hospital_id: UUID
    global_request_id: Optional[UUID] = None