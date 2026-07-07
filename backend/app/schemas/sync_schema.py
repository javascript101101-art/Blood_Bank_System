from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Any

class SyncQueueItem(BaseModel):
    id: UUID
    table_name: str
    record_id: UUID
    operation: str
    data: dict
    status: str
    created_at: datetime

class SyncPushRequest(BaseModel):
    hospital_id: UUID
    items: List[SyncQueueItem]

class SyncPushResponse(BaseModel):
    success: List[UUID]
    failed: List[UUID]
    conflicts: List[dict]

class SyncStatusResponse(BaseModel):
    pending_count: int
    synced_count: int
    failed_count: int
    conflict_count: int
    last_sync_at: Optional[datetime] = None  # <--- ဒီမှာ default None ထည့်ပါ