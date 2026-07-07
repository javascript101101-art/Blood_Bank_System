from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any

class SyncQueueItem(BaseModel):
    id: UUID
    table_name: str
    record_id: UUID
    operation: str  # INSERT, UPDATE, DELETE
    data: Dict[str, Any]
    status: str
    created_at: datetime

class SyncPushRequest(BaseModel):
    hospital_id: UUID
    items: List[SyncQueueItem]

class SyncPushResponse(BaseModel):
    success: List[UUID]   # အောင်မြင်သွားသော Local Sync ID များ
    failed: List[UUID]    # မအောင်မြင်သော ID များ
    conflicts: List[Dict[str, Any]]  # Conflict ဖြစ်သော ID နှင့် အသေးစိတ်