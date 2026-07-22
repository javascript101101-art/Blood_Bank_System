from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class HospitalRequestCreate(BaseModel):
    hospital_name: str
    address: Optional[str] = None
    contact_email: EmailStr

class HospitalRequestResponse(BaseModel):
    id: str
    hospital_name: str
    address: Optional[str] = None
    contact_email: str
    status: str
    rejection_reason: Optional[str] = None
    hospital_id: Optional[str] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True