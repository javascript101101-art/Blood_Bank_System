from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from uuid import UUID
from typing import Optional

# ============================================
# Create Schema
# ============================================
class BloodRequestCreate(BaseModel):
    blood_component: str = Field(..., min_length=1, max_length=50, example="Red_Cells")
    blood_group: str = Field(..., min_length=1, max_length=20, example="A Positive")
    quantity_units: int = Field(..., gt=0, example=2)
    urgency: Optional[str] = Field("Normal Request", max_length=50)
    required_date: date
    patient_condition: Optional[str] = None

# ============================================
# Update Schema (အကုန်လုံး Optional ဖြစ်ရမည်)
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
    urgency: Optional[str] = Field(None, max_length=50)
    required_date: Optional[date] = None
    patient_condition: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(Pending|Approved|Fulfilled|Rejected)$")

# ============================================
# Response Schema (Database မှ Data ပြန်ထုတ်ပေးရန်)
# ============================================
class BloodRequestResponse(BaseModel):
    id: UUID
    hospital_id: UUID
    requested_by_user_id: UUID
    
    # 🏥 CLINIC / HOSPITAL INFORMATION
    clinic_name: str
    license: str
    contact_phone: str
    contact_email: EmailStr
    clinic_address: str

    # 🩸 BLOOD REQUEST DETAILS
    blood_component: Optional[str] = "Whole_Blood"
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