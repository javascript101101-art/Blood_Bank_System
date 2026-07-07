from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.sync_service_global import GlobalSyncService
from app.schemas.sync_schema import SyncPushRequest, SyncPushResponse

router = APIRouter(prefix="/sync", tags=["Sync (Global)"])

@router.post("/push", response_model=SyncPushResponse)
def sync_push_global(
    payload: SyncPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))  # Global Admin သာ Push လက်ခံရန်
):
    """
    Local Hospital Server မှ Sync Data ကို လက်ခံပါသည်။
    """
    result = GlobalSyncService.process_push(
        db=db,
        hospital_id=payload.hospital_id,
        items=payload.items
    )
    return result