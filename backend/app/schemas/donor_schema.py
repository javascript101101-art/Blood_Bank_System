from pydantic import BaseModel, Field
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