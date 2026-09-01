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
from app.services.global_inventory_service import GlobalInventoryService # 🟢 Service ကို Import လုပ်ပါသည်

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
        GlobalInventory.blood_component,
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor,
        func.sum(GlobalInventory.quantity_ml).label("total_ml")
    ).filter(
        GlobalInventory.quantity_ml > 0,
        GlobalInventory.status == "Available", # 🟢 Available ဖြစ်သည်များကိုသာ တွက်ချက်ရန်
        GlobalInventory.blood_component != "Whole_Blood" 
    ).group_by(
        GlobalInventory.blood_component,
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor
    ).all()
    
    result = []
    for item in summary:
        result.append({
            "blood_component": item.blood_component, 
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
# 🟢 (၃) အိတ်ဆိုလျှင် (၃) ခု ပြန်ထုတ်ပေးမည်ဖြစ်၍ response_model ကို List ပြောင်းထားပါသည်
@router.post("/", response_model=List[GlobalInventoryResponse], status_code=status.HTTP_201_CREATED)
def add_blood_to_global(
    payload: GlobalInventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Admin မှ သွေးအသစ်ကို Inventory သို့ တိုက်ရိုက်ထည့်သွင်းခြင်း (Bulk Insert ပါဝင်သည်)"""
    try:
        # 🟢 Service ထဲရှိ add_blood ကို အသုံးပြု၍ Data အားလုံး လှမ်းပို့ပါမည်
        added_inventories = GlobalInventoryService.add_blood(
            db=db,
            blood_component=payload.blood_component,
            blood_group=payload.blood_group,
            rh_factor=payload.rh_factor,
            quantity_ml=payload.quantity_ml,
            source_hospital_id=payload.source_hospital_id,
            source_request_id=payload.source_request_id,
            unit_id=payload.unit_id,
            supplier=payload.supplier,           # 🟢 Supplier အမည်
            expiry_date=payload.expiry_date,     # 🟢 သက်တမ်းကုန်ဆုံးရက်
            number_of_units=payload.number_of_units # 🟢 အိတ်အရေအတွက် (Loop ပတ်ရန်)
        )
        return added_inventories
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"သွေးထည့်သွင်းခြင်း မအောင်မြင်ပါ: {str(e)}"
        )

# ==========================================
# ၄။ Low Stock Warning (Global Central Stock အတွက်)
# ==========================================
@router.get("/low-stock-warnings")
def get_global_low_stock_warnings(
    threshold: float = 100.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Central Stock တွင် သတ်မှတ်ထားသော ပမာဏအောက် ရောက်နေသော သွေးများကို သတိပေးရန်"""
    summary = db.query(
        GlobalInventory.blood_component, 
        GlobalInventory.blood_group,
        GlobalInventory.rh_factor,
        func.sum(GlobalInventory.quantity_ml).label("total_ml")
    ).filter(
        GlobalInventory.quantity_ml > 0,
        GlobalInventory.status == "Available", # 🟢
        GlobalInventory.blood_component != "Whole_Blood"
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