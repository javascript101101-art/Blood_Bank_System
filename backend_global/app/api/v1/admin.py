from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.admin_service import AdminService
from app.schemas.admin_schema import GlobalStats, SyncLogEntry
from typing import List

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats", response_model=GlobalStats)
def get_global_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Dashboard အတွက် စုစုပေါင်း Statistic များကို ပြန်ပေးသည်"""
    return AdminService.get_global_stats(db)

@router.get("/sync-logs", response_model=List[SyncLogEntry])
def get_sync_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Sync Logs များကို ပြန်ပေးသည် (နောက်ဆုံး ၅၀ ခု)"""
    return AdminService.get_sync_logs(db, limit)