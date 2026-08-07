from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from uuid import UUID
from typing import Optional

# ============================================
# 🆕 Create Schema (Frontend မှ ပို့မည့် Data များသာ ပါမည်)
# ============================================
class BloodRequestCreate(BaseModel):
    # 🚫 Clinic Data များကို ဖယ်ရှားထားပါသည် (Backend မှ Auto ဖြည့်မည်ဖြစ်သောကြောင့်)
    
    # 🩸 BLOOD REQUEST DETAILS
    blood_group: str = Field(..., min_length=1, max_length=20, example="A Positive")
    quantity_units: int = Field(..., gt=0, example=2)
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
    
    blood_group: Optional[str] = Field(None, min_length=1, max_length=20)
    quantity_units: Optional[int] = Field(None, gt=0)
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
    blood_group: str
    quantity_units: int
    urgency: Optional[str] = None
    required_date: date
    patient_condition: Optional[str] = None
    status: str
    
    requested_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True