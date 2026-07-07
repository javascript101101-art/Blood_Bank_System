from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID
from typing import Optional

class InventoryBase(BaseModel):
    blood_group: str = Field(..., pattern="^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern="^(Positive|Negative)$")
    quantity_ml: int = Field(..., ge=0)
    expiry_date: date
    status: Optional[str] = Field("Available", pattern="^(Available|Expired|Quarantined)$")

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    id: UUID
    hospital_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True