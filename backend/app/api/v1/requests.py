from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.request_service import RequestService
from app.schemas.request_schema import BloodRequestCreate, BloodRequestUpdate, BloodRequestResponse

router = APIRouter(prefix="/requests", tags=["Blood Requests"])

@router.post("/", response_model=BloodRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    req_data: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလိုအပ်ချက်အသစ် တင်သွင်းရန်"""
    return RequestService.create_request(db, req_data, current_user.hospital_id, current_user.id)

@router.get("/", response_model=List[BloodRequestResponse])
def get_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးလိုအပ်ချက်အားလုံး ကြည့်ရန်"""
    return RequestService.get_requests(db, current_user.hospital_id)

@router.get("/{req_id}", response_model=BloodRequestResponse)
def get_request(
    req_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးလိုအပ်ချက်တစ်ခု ကြည့်ရန်"""
    request = RequestService.get_request(db, req_id, current_user.hospital_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@router.put("/{req_id}", response_model=BloodRequestResponse)
def update_request(
    req_id: UUID,
    req_data: BloodRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလိုအပ်ချက် ပြင်ဆင်ရန် (ဥပမာ - Status ပြောင်းရန်)"""
    request = RequestService.update_request(db, req_id, current_user.hospital_id, req_data)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@router.delete("/{req_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    req_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလိုအပ်ချက် ဖျက်ရန်"""
    deleted = RequestService.delete_request(db, req_id, current_user.hospital_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Request not found")
    return None