from pydantic import BaseModel, Field, EmailStr
from datetime import date, datetime
from uuid import UUID
from typing import Optional

class BloodRequestBase(BaseModel):
    # 🏥 CLINIC / HOSPITAL INFORMATION
    clinic_name: str = Field(..., min_length=1, max_length=255, example="City Health Clinic")
    license: str = Field(..., min_length=1, max_length=100, example="REG-102938")
    contact_phone: str = Field(..., min_length=1, max_length=50, example="09xxxxxxxxx")
    contact_email: EmailStr = Field(..., example="clinic@example.com")
    clinic_address: str = Field(..., min_length=1, example="Street, Township, City")

    # 🩸 BLOOD REQUEST DETAILS
    blood_group: str = Field(..., min_length=1, max_length=20, example="A Positive")
    quantity_units: int = Field(..., gt=0, example=2)
    urgency: Optional[str] = Field("Normal Request", max_length=50)
    required_date: date
    patient_condition: Optional[str] = None
    
    # Tracking Status
    status: Optional[str] = Field("Pending", pattern="^(Pending|Approved|Fulfilled|Rejected)$")

class BloodRequestCreate(BloodRequestBase):
    pass

# ============================================
# 🆕 Update Schema - အကုန်လုံး Optional ဖြစ်ရမယ်
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

class BloodRequestResponse(BloodRequestBase):
    id: UUID
    hospital_id: UUID
    requested_by_user_id: UUID
    requested_at: Optional[datetime]
    fulfilled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True