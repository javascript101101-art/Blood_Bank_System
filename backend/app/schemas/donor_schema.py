from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from uuid import UUID
from typing import Optional

class DonorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    dob: Optional[date] = None
    blood_group: str = Field(..., pattern="^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern="^(Positive|Negative)$")
    contact_phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    last_donation_date: Optional[date] = None
    donation_quantity: int = Field(..., ge=100, le=600)  # ✅ REQUIRED

    @validator('donation_quantity')
    def validate_quantity(cls, v):
        if v < 100 or v > 600:
            raise ValueError('Donation quantity must be between 100ml and 600ml')
        return v

class DonorCreate(DonorBase):
    pass

class DonorUpdate(DonorBase):
    pass

class DonorResponse(DonorBase):
    id: UUID
    hospital_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True