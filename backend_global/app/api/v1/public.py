from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.hospital_request import HospitalRequestCreate, HospitalRequestResponse
from app.services.hospital_service import HospitalService

router = APIRouter(prefix="/public", tags=["Public"])

@router.post("/register", response_model=HospitalRequestResponse)
def register_hospital(
    data: HospitalRequestCreate,
    db: Session = Depends(get_db)
):
    """ဆေးရုံအသစ်က ဒီ Endpoint ကို သုံးပြီး Register လျှောက်ထားနိုင်တယ် (JWT မလိုဘူး)"""
    new_request = HospitalService.create_request(db, data)
    return new_request