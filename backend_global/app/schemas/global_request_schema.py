from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class GlobalBloodRequestBase(BaseModel):
    # 🟢 "A Positive" ကဲ့သို့ စာလုံးများ လက်ခံနိုင်စေရန် pattern ကို ဖြုတ်ထားပါသည်
    blood_group: str = Field(...)
    rh_factor: str = Field(...)
    
    # 🆕 Component အသစ် ထည့်သွင်းထားပါသည် (မပါလာပါက Whole_Blood ဟု ယူဆမည်)
    blood_component: Optional[str] = Field(default="Whole_Blood")
    
    quantity_ml: int = Field(..., gt=0)
    urgency: Optional[str] = Field("Normal", pattern="^(Critical|Urgent|Normal)$")
    request_note: Optional[str] = None
    
    # ==========================================
    # 🟢 [အရေးကြီးဆုံး] ဒီမှာ Unit ID တွေသယ်သွားဖို့ Field ကို မဖြစ်မနေ ထည့်ရပါမည်
    # ==========================================
    fulfilled_unit_ids: Optional[str] = None

class GlobalBloodRequestCreate(GlobalBloodRequestBase):
    pass

class GlobalBloodRequestUpdate(BaseModel):
    blood_group: Optional[str] = Field(None)
    rh_factor: Optional[str] = Field(None)
    
    # 🆕 Component ကို ပြင်ဆင်နိုင်ရန် ထည့်ထားပါသည်
    blood_component: Optional[str] = Field(None)
    
    quantity_ml: Optional[int] = Field(None, gt=0)
    urgency: Optional[str] = Field(None, pattern="^(Critical|Urgent|Normal)$")
    
    # 🟢 Status များ
    status: Optional[str] = Field(None, pattern="^(Pending|Assigned|Approved|Fulfilled|Supplier_Fulfilled|SUPPLIER_FULFILLED|In-Transit|IN-TRANSIT|Delivered|DELIVERED|Rejected)$")
    
    assigned_hospital_id: Optional[UUID] = None
    request_note: Optional[str] = None
    
    # 🟢 [အရေးကြီးဆုံး] Update လုပ်ရာတွင်လည်း Unit ID များကို လက်ခံနိုင်ရန် ထည့်ရပါမည်
    fulfilled_unit_ids: Optional[str] = None

class GlobalBloodRequestResponse(GlobalBloodRequestBase):
    id: UUID
    requesting_hospital_id: UUID
    assigned_hospital_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True