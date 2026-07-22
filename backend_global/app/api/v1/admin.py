from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.models.donor import Donor          # 🆕 Import Donor
from app.models.inventory import Inventory  # 🆕 Import Inventory
from app.models.blood_request import BloodRequest  # 🆕 Import BloodRequest
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
# 🆕 5. Get All Requests (All Hospitals)
# ============================================
@router.get("/requests")
def get_all_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Global_Admin"))
):
    """ဆေးရုံအားလုံးရဲ့ Blood Request စာရင်းကို ပြန်ပေးပါ"""
    requests = db.query(BloodRequest).all()
    return requests