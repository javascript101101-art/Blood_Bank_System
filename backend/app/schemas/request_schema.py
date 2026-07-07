from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class BloodRequestBase(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=255)
    blood_group: str = Field(..., pattern="^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern="^(Positive|Negative)$")
    quantity_ml: int = Field(..., gt=0)
    urgency: Optional[str] = Field("Normal", pattern="^(Critical|Urgent|Normal)$")
    status: Optional[str] = Field("Pending", pattern="^(Pending|Approved|Fulfilled|Rejected)$")

class BloodRequestCreate(BloodRequestBase):
    pass

class BloodRequestUpdate(BloodRequestBase):
    pass

class BloodRequestResponse(BloodRequestBase):
    id: UUID
    hospital_id: UUID
    requested_by_user_id: UUID
    requested_at: datetime
    fulfilled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True