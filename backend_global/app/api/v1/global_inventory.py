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
    """သွေးအုပ်စု၊ Rh Factor နှင့် Component အလိုက် စုစုပေါင်း သွေးပမာဏကို တွက်ချက်ပေးခြင်း"""
    summary = db.query(
        GlobalInventory.blood_component, # 🟢 Component ပါ ထည့်သွင်းထားပါသည်
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor,
        func.sum(GlobalInventory.quantity_ml).label("total_ml")
    ).filter(
        GlobalInventory.quantity_ml > 0,
        GlobalInventory.blood_component != "Whole_Blood" # 🟢 Whole Blood ဖယ်ထုတ်ရန်
    ).group_by(
        GlobalInventory.blood_component,
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor
    ).all()
    
    # Null ဖြစ်နေတဲ့ total_ml တွေကို 0 အဖြစ် ပြောင်းပေးရန် (Safety check)
    result = []
    for item in summary:
        result.append({
            "blood_component": item.blood_component, # 🟢 ဤနေရာတွင် ထည့်ပေးလိုက်ပါသည်
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
            blood_component=payload.blood_component, # 🟢 Payload မှ Component ကို ထည့်သွင်းမည်
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

# ==========================================
# 🆕 ၄။ Low Stock Warning (Global Central Stock အတွက်)
# ==========================================
@router.get("/low-stock-warnings")
def get_global_low_stock_warnings(
    threshold: float = 100.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Central Stock တွင် သတ်မှတ်ထားသော ပမာဏအောက် (ဥပမာ - ၁၀၀ ml) ရောက်နေသော သွေးများကို သတိပေးရန်"""
    
    # GROUP BY လုပ်ပြီး SUM တွက်ချက်ကာ threshold အောက် ငယ်သည်များကိုသာ HAVING ဖြင့် Filter လုပ်ပါသည်
    summary = db.query(
        GlobalInventory.blood_component, # 🟢 Component ပါ ထည့်သွင်းထားပါသည်
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor,
        func.sum(GlobalInventory.quantity_ml).label("total_ml")
    ).filter(
        GlobalInventory.quantity_ml > 0,
        GlobalInventory.blood_component != "Whole_Blood" # 🟢 Whole Blood ဖယ်ထုတ်ရန်
    ).group_by(
        GlobalInventory.blood_component,
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor
    ).having(func.sum(GlobalInventory.quantity_ml) < threshold).all()

    warnings = []
    for item in summary:
        current_total = item.total_ml or 0
        comp_name = item.blood_component.replace('_', ' ').title()
        warnings.append({
            "blood_component": item.blood_component,
            "blood_type": f"{item.blood_group} {item.rh_factor}",
            "blood_group": item.blood_group,
            "rh_factor": item.rh_factor,
            "total_quantity": current_total,
            "warning_message": f"Central Stock Warning: {item.blood_group} {item.rh_factor} ({comp_name}) is running low ({current_total} ml remaining)."
        })
        
    return {"alerts": warnings}