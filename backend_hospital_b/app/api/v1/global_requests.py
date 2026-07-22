from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.global_request_service import GlobalRequestService
from app.schemas.global_request_schema import GlobalBloodRequestCreate, GlobalBloodRequestUpdate, GlobalBloodRequestResponse

router = APIRouter(prefix="/global-requests", tags=["Global Blood Requests"])

@router.post("/", response_model=GlobalBloodRequestResponse, status_code=status.HTTP_201_CREATED)
def create_global_request(
    req_data: GlobalBloodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    return GlobalRequestService.create_global_request(db, req_data, current_user.hospital_id)

# 🆕 Local Hospital က သူ့ရဲ့ Request တွေကို ကြည့်ရန်
@router.get("/", response_model=List[GlobalBloodRequestResponse])
def get_local_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))  # Hospital_Admin ပဲကြည့်လို့ရ
):
    return GlobalRequestService.get_local_requests(db, current_user.hospital_id)

@router.get("/all", response_model=List[GlobalBloodRequestResponse])
def get_all_global_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    return GlobalRequestService.get_all_requests(db)

@router.put("/{req_id}", response_model=GlobalBloodRequestResponse)
def update_global_request(
    req_id: UUID,
    req_data: GlobalBloodRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    request = GlobalRequestService.update_request(db, req_id, req_data)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request