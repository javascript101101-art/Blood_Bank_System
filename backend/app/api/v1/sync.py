from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.sync_service import SyncService
from app.schemas.sync_schema import SyncStatusResponse

# ============================================
# Sync Payload Schemas (Data လက်ခံရန်)
# ============================================
class SyncItemSchema(BaseModel):
    id: str
    table_name: str
    record_id: str
    operation: str
    data: Dict[str, Any]
    status: str
    created_at: str

class SyncPayloadSchema(BaseModel):
    hospital_id: str
    items: List[SyncItemSchema]

router = APIRouter(prefix="/sync", tags=["Sync"])

@router.post("/push")
def sync_push(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """Local Data ကို Global Server ဆီ Push လုပ်ပါ (Pull ကိုပါ တွဲလုပ်ပါမည်)"""
    # ၁။ အရင်ဆုံး Local က Data တွေကို Global ဆီ ပို့မယ် (Push)
    push_result = SyncService.push_to_global(db, current_user.hospital_id)
    
    # ၂။ ပြီးတာနဲ့ Global က Data အသစ်တွေကို Local ဆီ ပြန်ဆွဲယူမယ် (Pull)
    pull_result = SyncService.pull_from_global(db, current_user.hospital_id)
    
    return {
        "push_result": push_result,
        "pull_result": pull_result
    }

# ==========================================
# 🆕 အသစ်ထပ်ထည့်ထားသော Pull သီးသန့် Endpoint
# ==========================================
@router.post("/pull")
def sync_pull(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """Global Server မှ Data အသစ်များ (Status အပြောင်းအလဲများ) ကို သီးသန့်ဆွဲယူရန်"""
    result = SyncService.pull_from_global(db, current_user.hospital_id)
    return result

@router.get("/status", response_model=SyncStatusResponse)
def sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync Status ကို ကြည့်ရန်"""
    return SyncService.get_sync_status(db, current_user.hospital_id)

@router.post("/receive")
def sync_receive(
    payload: SyncPayloadSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Global Server မှ Local Data များကို လက်ခံသိမ်းဆည်းမည့် Endpoint"""
    result = SyncService.receive_from_local(db, payload.model_dump())
    return result