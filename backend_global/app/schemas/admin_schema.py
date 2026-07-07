from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class HospitalStats(BaseModel):
    hospital_id: UUID
    name: str
    location: Optional[str]
    donor_count: int
    inventory_count: int
    request_count: int

class GlobalStats(BaseModel):
    total_donors: int
    total_inventory: int
    total_requests: int
    total_hospitals: int
    hospitals: List[HospitalStats]

class SyncLogEntry(BaseModel):
    id: UUID
    status: str
    error_message: Optional[str]
    sync_timestamp: str