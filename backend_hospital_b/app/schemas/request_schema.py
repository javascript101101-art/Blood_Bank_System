from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from uuid import UUID
from typing import Optional, List

# ============================================
# 🟢 Traceability အတွက် သွေးအိတ်အချက်အလက် (Nested Schema)
# ============================================
class FulfilledInventorySnippet(BaseModel):
    id: UUID
    unit_id: Optional[str] = None
    blood_component: str
    quantity_ml: int

    class Config:
        from_attributes = True

# ============================================
# 🆕 Create Schema (Frontend မှ ပို့မည့် Data များသာ ပါမည်)
# ============================================
class BloodRequestCreate(BaseModel):
    # 🚫 Clinic Data များကို ဖယ်ရှားထားပါသည် (Backend မှ Auto ဖြည့်မည်ဖြစ်သောကြောင့်)
    
    # 🩸 BLOOD REQUEST DETAILS
    blood_component: str = Field(..., min_length=1, max_length=50, example="Red_Cells")
    blood_group: str = Field(..., min_length=1, max_length=20, example="A Positive")
    quantity_units: int = Field(..., gt=0, example=2)
    
    # 🟢 [အရေးကြီးဆုံး ပြင်ဆင်ချက်] ဒါလေးမပါရင် Frontend ကပို့တဲ့ 200ml ကို လက်မခံဘဲ 500 အဖြစ် ပြောင်းသွားပါမည်
    volume_per_unit_ml: int = Field(default=500, gt=0, example=200) 
    
    urgency: Optional[str] = Field("Normal Request", max_length=50)
    required_date: date
    patient_condition: Optional[str] = None
    # Status ကို Backend က "Pending" ဟု Auto သတ်မှတ်ပေးမည်ဖြစ်၍ ဤနေရာတွင် မလိုပါ။

# ============================================
# 🆕 Update Schema (အကုန်လုံး Optional ဖြစ်ရမည်)
# ============================================
class BloodRequestUpdate(BaseModel):
    clinic_name: Optional[str] = Field(None, min_length=1, max_length=255)
    license: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_phone: Optional[str] = Field(None, min_length=1, max_length=50)
    contact_email: Optional[EmailStr] = None
    clinic_address: Optional[str] = Field(None, min_length=1)
    
    blood_component: Optional[str] = Field(None, min_length=1, max_length=50)
    blood_group: Optional[str] = Field(None, min_length=1, max_length=20)
    quantity_units: Optional[int] = Field(None, gt=0)
    
    # 🟢 [အသစ်] Update လုပ်ရာတွင်လည်း လက်ခံနိုင်ရန်
    volume_per_unit_ml: Optional[int] = Field(None, gt=0)
    fulfilled_unit_ids: Optional[str] = None
    
    urgency: Optional[str] = Field(None, max_length=50)
    required_date: Optional[date] = None
    patient_condition: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(Pending|Approved|Fulfilled|Rejected)$")

# ============================================
# 🆕 Response Schema (Database မှ Data အားလုံး အပြည့်အစုံ ပြန်ထုတ်ပေးမည်)
# ============================================
class BloodRequestResponse(BaseModel):
    id: UUID
    hospital_id: UUID
    requested_by_user_id: UUID
    
    # 🏥 CLINIC / HOSPITAL INFORMATION (Response တွင် ပါဝင်ရမည်)
    clinic_name: str
    license: str
    contact_phone: str
    contact_email: EmailStr
    clinic_address: str

    # 🩸 BLOOD REQUEST DETAILS
    blood_component: Optional[str] = "Whole_Blood" 
    blood_group: str
    quantity_units: int
    
    # 🟢 [အသစ်] Database ထဲမှ ml ပမာဏကို Frontend သို့ ပြန်ထုတ်ပေးရန်
    volume_per_unit_ml: int = 500
    fulfilled_unit_ids: Optional[str] = None
    
    urgency: Optional[str] = None
    required_date: date
    patient_condition: Optional[str] = None
    status: str
    
    # 🟢 Traceability - ဤ Request အတွက် ထုတ်ပေးလိုက်သော သွေးအိတ်များ (Unit IDs) စာရင်း
    fulfilled_inventories: List[FulfilledInventorySnippet] = []
    
    requested_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True