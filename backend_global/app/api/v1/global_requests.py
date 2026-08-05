from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.global_request_service import GlobalRequestService
from app.schemas.global_request_schema import GlobalBloodRequestCreate, GlobalBloodRequestUpdate, GlobalBloodRequestResponse

router = APIRouter(prefix="/global-requests", tags=["Global Blood Requests"])

# Assign လုပ်ရန်အတွက် လိုအပ်သော Payload Schema
class AssignRequestPayload(BaseModel):
    hospital_id: UUID

# ============================================
# Global Admin က Request အကုန်ကြည့်ခြင်း
# ============================================
@router.get("/", response_model=List[GlobalBloodRequestResponse])
def get_all_global_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    return GlobalRequestService.get_all_requests(db)

# ============================================
# Global Admin က Request တစ်ခုကို Update လုပ်ခြင်း (Basic Update)
# ============================================
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

# ============================================
# 🆕 Global Admin -> Supplier Hospital (Hospital B) ကို Assign လုပ်ခြင်း
# ============================================
@router.post("/{req_id}/assign", response_model=GlobalBloodRequestResponse)
def assign_global_request(
    req_id: UUID,
    payload: AssignRequestPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    return GlobalRequestService.assign_request(db, req_id, payload.hospital_id)

# ============================================
# 🆕 Supplier Hospital မှ သွေးပေးပို့မှုကို Fulfilled အဖြစ် သတ်မှတ်ခြင်း (Global Inventory ထဲဝင်မည်)
# ============================================
@router.post("/{req_id}/fulfill", response_model=GlobalBloodRequestResponse)
def fulfill_global_request(
    req_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    return GlobalRequestService.fulfill_request(db, req_id)

# ============================================
# 🆕 Global Admin -> Requesting Hospital (Hospital A) သို့ သွေးပို့ခြင်း (Global Inventory မှ နှုတ်မည်)
# ============================================
@router.post("/{req_id}/deliver", response_model=GlobalBloodRequestResponse)
def deliver_global_request(
    req_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    return GlobalRequestService.deliver_request(db, req_id)