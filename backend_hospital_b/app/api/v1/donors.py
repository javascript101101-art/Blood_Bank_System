from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.donor_service import DonorService
from app.schemas.donor_schema import DonorCreate, DonorUpdate, DonorResponse

router = APIRouter(prefix="/donors", tags=["Donors"])

@router.post("/", response_model=DonorResponse, status_code=status.HTTP_201_CREATED)
def create_donor(
    donor_data: DonorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလှူရှင်အသစ် ထည့်သွင်းရန်"""
    return DonorService.create_donor(db, donor_data, current_user.hospital_id)

@router.get("/", response_model=List[DonorResponse])
def get_donors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးလှူရှင်အားလုံး ကြည့်ရန်"""
    return DonorService.get_donors(db, current_user.hospital_id)

@router.get("/{donor_id}", response_model=DonorResponse)
def get_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးလှူရှင်တစ်ဦးကို ကြည့်ရန်"""
    donor = DonorService.get_donor(db, donor_id, current_user.hospital_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.put("/{donor_id}", response_model=DonorResponse)
def update_donor(
    donor_id: UUID,
    donor_data: DonorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလှူရှင်အချက်အလက် ပြင်ဆင်ရန်"""
    donor = DonorService.update_donor(db, donor_id, current_user.hospital_id, donor_data)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    return donor

@router.delete("/{donor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_donor(
    donor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးလှူရှင်ကို ဖျက်ရန်"""
    deleted = DonorService.delete_donor(db, donor_id, current_user.hospital_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Donor not found")
    return None