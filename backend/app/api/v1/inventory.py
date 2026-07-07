from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user, role_required
from app.models.user import User
from app.services.inventory_service import InventoryService
from app.schemas.inventory_schema import InventoryCreate, InventoryUpdate, InventoryResponse

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