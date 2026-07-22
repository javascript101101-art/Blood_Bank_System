from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class GlobalBloodRequestBase(BaseModel):
    blood_group: str = Field(..., pattern="^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern="^(Positive|Negative)$")
    quantity_ml: int = Field(..., gt=0)
    urgency: Optional[str] = Field("Normal", pattern="^(Critical|Urgent|Normal)$")
    request_note: Optional[str] = None

class GlobalBloodRequestCreate(GlobalBloodRequestBase):
    pass

class GlobalBloodRequestUpdate(BaseModel):
    blood_group: Optional[str] = Field(None, pattern="^(A|B|AB|O)$")
    rh_factor: Optional[str] = Field(None, pattern="^(Positive|Negative)$")
    quantity_ml: Optional[int] = Field(None, gt=0)
    urgency: Optional[str] = Field(None, pattern="^(Critical|Urgent|Normal)$")
    status: Optional[str] = Field(None, pattern="^(Pending|Assigned|Approved|Fulfilled|Rejected)$")
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