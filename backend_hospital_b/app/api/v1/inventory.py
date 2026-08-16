from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.inventory_service import InventoryService
from app.schemas.inventory_schema import InventoryCreate, InventoryUpdate, InventoryResponse, InventorySplitRequest

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory(
    inv_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးတိုက်စာရင်းအသစ် ထည့်သွင်းရန်"""
    return InventoryService.create_inventory(db, inv_data, current_user.hospital_id)

@router.get("/", response_model=List[InventoryResponse])
def get_inventories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးတိုက်စာရင်းအားလုံး ကြည့်ရန်"""
    return InventoryService.get_inventories(db, current_user.hospital_id)

# ============================================
# Low Stock Warnings (Local Hospital)
# ============================================
@router.get("/low-stock-warnings")
def get_local_low_stock_warnings(
    threshold: float = 500.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Local Hospital ၏ Inventory တွင် သတ်မှတ်ထားသော ပမာဏအောက် ရောက်နေသော သွေးများကို သတိပေးရန်"""
    warnings = InventoryService.get_low_stock_warnings(db, current_user.hospital_id, threshold)
    return {"alerts": warnings}

# ============================================
# 🆕 ဆေးခန်း (Clinic) များအတွက် Available Inventory 
# ============================================
@router.get("/available", response_model=List[InventoryResponse])
def get_available_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ဆေးခန်းများမှ Request တင်ရန် ရရှိနိုင်သော (Available) သွေးများကိုသာ ပြသရန်"""
    # အရင်ဆုံး Inventory အားလုံးကို ယူပါမည်
    inventories = InventoryService.get_inventories(db, current_user.hospital_id)
    # Status 'Available' ဖြစ်နေသော သွေးများကိုသာ စစ်ထုတ် (Filter) ပြီး ပြန်ပို့ပေးပါမည်
    available_only = [inv for inv in inventories if inv.status == "Available"]
    return available_only

# ============================================
# 🆕 Component Splitting Endpoint (သွေးခွဲထုတ်ရန်)
# ============================================
@router.post("/{inv_id}/split", response_model=List[InventoryResponse])
def split_inventory(
    inv_id: UUID,
    split_data: InventorySplitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """Quarantined သွေးအိတ်စိမ်းကို သွေးအစိတ်အပိုင်းများအဖြစ် ခွဲထုတ်ရန်"""
    result = InventoryService.split_inventory(db, inv_id, current_user.hospital_id, split_data)
    if not result:
        raise HTTPException(status_code=400, detail="သွေးခွဲထုတ်ခြင်း မအောင်မြင်ပါ။ (သွေးအိတ်သည် Quarantined အခြေအနေဖြစ်ရန် လိုအပ်သည်)")
    return result

# ⚠️ သတိပြုရန် - `/{inv_id}` သည် `/available` ၏ အောက်တွင်သာ ရှိရပါမည်။
@router.get("/{inv_id}", response_model=InventoryResponse)
def get_inventory(
    inv_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """သွေးတိုက်စာရင်းတစ်ခု ကြည့်ရန်"""
    inventory = InventoryService.get_inventory(db, inv_id, current_user.hospital_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory

@router.put("/{inv_id}", response_model=InventoryResponse)
def update_inventory(
    inv_id: UUID,
    inv_data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးတိုက်စာရင်း ပြင်ဆင်ရန်"""
    inventory = InventoryService.update_inventory(db, inv_id, current_user.hospital_id, inv_data)
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return inventory

@router.delete("/{inv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(
    inv_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """သွေးတိုက်စာရင်း ဖျက်ရန်"""
    deleted = InventoryService.delete_inventory(db, inv_id, current_user.hospital_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Inventory not found")
    return None