from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class GlobalBloodRequestBase(BaseModel):
    # 🔴 Frontend မှ "A Positive" ကဲ့သို့ ပို့လာပါက Error မတက်စေရန် pattern ကို ဖြုတ်ထားပါသည်
    blood_group: str = Field(...)
    rh_factor: str = Field(...)
    
    # 🆕 အခုမှ အသစ်ထပ်ထည့်လိုက်သော Component (မပို့ခဲ့လျှင် Whole_Blood ဟု ယူဆပါမည်)
    blood_component: Optional[str] = Field(default="Whole_Blood")
    
    quantity_ml: int = Field(..., gt=0)
    urgency: Optional[str] = Field("Normal", pattern="^(Critical|Urgent|Normal)$")
    request_note: Optional[str] = None

class GlobalBloodRequestCreate(GlobalBloodRequestBase):
    pass

class GlobalBloodRequestUpdate(BaseModel):
    blood_group: Optional[str] = Field(None)
    rh_factor: Optional[str] = Field(None)
    
    # 🆕 Component ကိုပါ ပြင်ချင်ပါက ပြင်နိုင်ရန် ထည့်ထားပါသည်
    blood_component: Optional[str] = Field(None)
    
    quantity_ml: Optional[int] = Field(None, gt=0)
    urgency: Optional[str] = Field(None, pattern="^(Critical|Urgent|Normal)$")
    status: Optional[str] = Field(None, pattern="^(Pending|Assigned|Approved|Fulfilled|Rejected|In-Transit|Delivered)$")
    assigned_hospital_id: Optional[UUID] = None
    request_note: Optional[str] = None

class GlobalBloodRequestResponse(GlobalBloodRequestBase):
    id: UUID
    requesting_hospital_id: UUID
    assigned_hospital_id: Optional[UUID]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True