from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.models.donor import Donor          
from app.models.inventory import Inventory  
from app.models.blood_request import BloodRequest 
from app.models.global_inventory import GlobalInventory # 🟢 Global Inventory ကို Import လုပ်ပါသည်
from app.services.admin_service import AdminService
from app.schemas.admin_schema import GlobalStats, SyncLogEntry
from app.schemas.request_schema import BloodRequestResponse 
from uuid import UUID 
from app.schemas.inventory_schema import InventoryResponse 

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================
# 1. Get Global Stats
# ============================================
@router.get("/stats", response_model=GlobalStats)
def get_global_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Dashboard အတွက် စုစုပေါင်း Statistic များကို ပြန်ပေးသည်"""
    return AdminService.get_global_stats(db)

# ============================================
# 2. Get Sync Logs
# ============================================
@router.get("/sync-logs", response_model=List[SyncLogEntry])
def get_sync_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Sync Logs များကို ပြန်ပေးသည် (နောက်ဆုံး ၅၀ ခု)"""
    return AdminService.get_sync_logs(db, limit)

# ============================================
# 3. Get All Donors (All Hospitals)
# ============================================
@router.get("/donors")
def get_all_donors(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံးရဲ့ Donor စာရင်းကို ပြန်ပေးပါ"""
    donors = db.query(Donor).all()
    return donors

# ============================================
# 🟢 4. Get All Inventory (Local + Global) ပြင်ဆင်ချက်
# ============================================
@router.get("/inventory")
def get_all_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံးရဲ့ Inventory နှင့် Global Inventory စာရင်းကို ပေါင်းပြီး ပြန်ပေးပါ"""
    
    # ၁။ Local Hospitals များမှ Inventory များ
    local_inventory = db.query(Inventory).all()
    
    # ၂။ Global Central Hub ၏ Inventory များ
    global_inventory = db.query(GlobalInventory).order_by(GlobalInventory.created_at.desc()).all()
    
    combined_inventory = []
    
    # Local Data များ ပေါင်းထည့်ခြင်း
    for item in local_inventory:
        combined_inventory.append({
            "id": str(item.id),
            "hospital_id": str(item.hospital_id) if item.hospital_id else None,
            "unit_id": item.unit_id,
            "blood_component": getattr(item, "blood_component", "Whole_Blood"),
            "blood_group": item.blood_group,
            "rh_factor": item.rh_factor,
            "quantity_ml": item.quantity_ml,
            "expiry_date": item.expiry_date,
            "status": item.status,
            "supplier": "Local Hospital" # 🟢 Local မှလာကြောင်း သတ်မှတ်သည်
        })
        
    # Global Data များ ပေါင်းထည့်ခြင်း
    for item in global_inventory:
        combined_inventory.append({
            "id": str(item.id),
            "hospital_id": None, # 🟢 Global Hub ဖြစ်ကြောင်း သိစေရန် None ထားမည်
            "unit_id": item.unit_id,
            "blood_component": getattr(item, "blood_component", "Whole_Blood"),
            "blood_group": item.blood_group,
            "rh_factor": item.rh_factor,
            "quantity_ml": item.quantity_ml,
            "expiry_date": getattr(item, "expiry_date", None),
            "status": getattr(item, "status", "Available"),
            "supplier": getattr(item, "supplier", "Global Hub") # 🟢 Supplier အမည် (သို့) Global Hub
        })
        
    return combined_inventory

# ============================================
# 5. Get Low Stock Warnings (Global)
# ============================================
@router.get("/low-stock-warnings")
def get_low_stock_warnings(
    threshold: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Inventory တွင် သတ်မှတ်ထားသော ပမာဏအောက် ရောက်နေသော သွေးအမျိုးအစားများကို ပြန်ပေးပါ"""
    warnings = AdminService.get_low_stock_warnings(db, threshold)
    return {"alerts": warnings}

# ============================================
# 6. Get All Hospitals (For ID to Name mapping in UI)
# ============================================
@router.get("/hospitals")
def get_all_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံး၏ ID နှင့် အမည်စာရင်းကို ပြန်ပေးပါ (UI မှ UUID များကို နာမည်ပြောင်းရန်)"""
    from app.models.hospital import Hospital
    hospitals = db.query(Hospital).all()
    return hospitals

# ============================================
# 7. Get Specific Donor History (Global Admin)
# ============================================
@router.get("/donors/{donor_id}/history", response_model=List[InventoryResponse])
def get_global_donor_history(
    donor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """Global Admin အတွက် အလှူရှင်တစ်ဦးချင်းစီ၏ သွေးလှူဒါန်းမှု မှတ်တမ်း (Traceability) ကို ကြည့်ရန်"""
    return AdminService.get_donor_history(db, donor_id)

# ============================================
# 8. Get All Blood Requests (Global Admin အတွက်)
# ============================================
@router.get("/requests", response_model=List[BloodRequestResponse])
def get_all_blood_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံးမှ သွေးတောင်းခံမှု အားလုံးကို ဆွဲထုတ်ရန်"""
    requests = db.query(BloodRequest).order_by(BloodRequest.requested_at.desc()).all()
    return requests