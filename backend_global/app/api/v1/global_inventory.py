from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.models.global_inventory import GlobalInventory
from app.schemas.global_inventory_schema import (
    GlobalInventoryCreate, 
    GlobalInventoryResponse, 
    GlobalInventorySummary
)

router = APIRouter(prefix="/global-inventory", tags=["Global Inventory"])

# ==========================================
# ၁။ သွေးလက်ကျန် အနှစ်ချုပ် (Summary) ကြည့်ရန်
# ==========================================
@router.get("/summary", response_model=List[GlobalInventorySummary])
def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """သွေးအုပ်စုနဲ့ Rh Factor အလိုက် စုစုပေါင်း သွေးပမာဏကို တွက်ချက်ပေးခြင်း"""
    summary = db.query(
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor,
        func.sum(GlobalInventory.quantity_ml).label("total_ml")
    ).group_by(
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor
    ).all()
    
    # Null ဖြစ်နေတဲ့ total_ml တွေကို 0 အဖြစ် ပြောင်းပေးရန် (Safety check)
    result = []
    for item in summary:
        result.append({
            "blood_group": item.blood_group,
            "rh_factor": item.rh_factor,
            "total_ml": item.total_ml or 0
        })
    return result

# ==========================================
# ၂။ သွေးလက်ကျန် အသေးစိတ်စာရင်း အားလုံးကြည့်ရန်
# ==========================================
@router.get("/", response_model=List[GlobalInventoryResponse])
def get_all_global_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Inventory အတွင်းရှိ သွေးစာရင်းအားလုံးကို နောက်ဆုံးထည့်ထားသည်မှစ၍ ပြသခြင်း"""
    return db.query(GlobalInventory).order_by(GlobalInventory.created_at.desc()).all()

# ==========================================
# ၃။ သွေးအသစ် ကိုယ်တိုင် (Manual) ထည့်သွင်းရန်
# ==========================================
@router.post("/", response_model=GlobalInventoryResponse, status_code=status.HTTP_201_CREATED)
def add_blood_to_global(
    payload: GlobalInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Admin မှ သွေးအသစ်ကို Inventory သို့ တိုက်ရိုက်ထည့်သွင်းခြင်း"""
    try:
        new_inventory = GlobalInventory(
            blood_group=payload.blood_group,
            rh_factor=payload.rh_factor,
            quantity_ml=payload.quantity_ml,
            source_hospital_id=payload.source_hospital_id,
            source_request_id=payload.source_request_id
        )
        db.add(new_inventory)
        db.commit()
        db.refresh(new_inventory)
        return new_inventory
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"သွေးထည့်သွင်းခြင်း မအောင်မြင်ပါ: {str(e)}"
        )