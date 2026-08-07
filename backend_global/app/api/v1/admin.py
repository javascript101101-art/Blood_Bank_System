from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.models.donor import Donor          # 🆕 Import Donor
from app.models.inventory import Inventory  # 🆕 Import Inventory
from app.services.admin_service import AdminService
from app.schemas.admin_schema import GlobalStats, SyncLogEntry

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
# 🆕 3. Get All Donors (All Hospitals)
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
# 🆕 4. Get All Inventory (All Hospitals)
# ============================================
@router.get("/inventory")
def get_all_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံးရဲ့ Inventory စာရင်းကို ပြန်ပေးပါ"""
    inventory = db.query(Inventory).all()
    return inventory

# ============================================
# 🆕 5. Get Low Stock Warnings (Global)
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