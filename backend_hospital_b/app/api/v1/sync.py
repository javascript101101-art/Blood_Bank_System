from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.sync_service import SyncService
from app.schemas.sync_schema import SyncStatusResponse

router = APIRouter(prefix="/sync", tags=["Sync"])

@router.post("/push")
def sync_push(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """Local Data ကို Global Server ဆီ Push လုပ်ပါ"""
    result = SyncService.push_to_global(db, current_user.hospital_id)
    return result

@router.get("/status", response_model=SyncStatusResponse)
def sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync Status ကို ကြည့်ရန်"""
    return SyncService.get_sync_status(db, current_user.hospital_id)