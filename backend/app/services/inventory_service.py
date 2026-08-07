from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from sqlalchemy import func
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.inventory_schema import InventoryCreate, InventoryUpdate

class InventoryService:
    @staticmethod
    def create_inventory(db: Session, inv_data: InventoryCreate, hospital_id: UUID) -> Inventory:
        # ၁။ ရှိပြီးသား Inventory ကို ရှာပါ
        existing = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.blood_group == inv_data.blood_group,
            Inventory.rh_factor == inv_data.rh_factor
        ).first()

        if existing:
            # ၂။ ရှိပြီးသား Item ဆိုရင် Quantity ကို တိုးပါ
            existing.quantity_ml += inv_data.quantity_ml
            # Expiry date ကို နောက်ဆုံးရက်နဲ့ Update လုပ်ပါ
            if inv_data.expiry_date > existing.expiry_date:
                existing.expiry_date = inv_data.expiry_date
            db.commit()
            db.refresh(existing)

            # ၃။ Update အတွက် Sync Queue ထဲထည့်ပါ
            InventoryService._add_to_sync_queue(db, existing, "UPDATE")
            return existing
        else:
            # ၄။ မရှိသေးရင် အသစ်ဆောက်ပါ
            inventory = Inventory(**inv_data.model_dump(), hospital_id=hospital_id)
            db.add(inventory)
            db.commit()
            db.refresh(inventory)

            InventoryService._add_to_sync_queue(db, inventory, "INSERT")
            return inventory

    @staticmethod
    def get_inventories(db: Session, hospital_id: UUID) -> List[Inventory]:
        return db.query(Inventory).filter(Inventory.hospital_id == hospital_id).all()

    @staticmethod
    def get_inventory(db: Session, inv_id: UUID, hospital_id: UUID) -> Optional[Inventory]:
        return db.query(Inventory).filter(Inventory.id == inv_id, Inventory.hospital_id == hospital_id).first()

    @staticmethod
    def update_inventory(db: Session, inv_id: UUID, hospital_id: UUID, inv_data: InventoryUpdate) -> Optional[Inventory]:
        inventory = InventoryService.get_inventory(db, inv_id, hospital_id)
        if not inventory:
            return None
        for key, value in inv_data.model_dump(exclude_unset=True).items():
            setattr(inventory, key, value)
        db.commit()
        db.refresh(inventory)

        InventoryService._add_to_sync_queue(db, inventory, "UPDATE")
        return inventory

    @staticmethod
    def delete_inventory(db: Session, inv_id: UUID, hospital_id: UUID) -> bool:
        inventory = InventoryService.get_inventory(db, inv_id, hospital_id)
        if not inventory:
            return False
        InventoryService._add_to_sync_queue(db, inventory, "DELETE", delete=True)
        db.delete(inventory)
        db.commit()
        return True

    # ============================================
    # 🆕 Low Stock Warnings Logic (Local Hospital)
    # ============================================
    @staticmethod
    def get_low_stock_warnings(db: Session, hospital_id: UUID, threshold: float = 500.0) -> List[dict]:
        """
        သတ်မှတ်ထားသော ဆေးရုံအတွက် သွေးအမျိုးအစားအလိုက် စုစုပေါင်းပမာဏကို တွက်ချက်ပြီး 
        threshold (ဥပမာ - 500 ml) အောက် ရောက်နေသော သွေးများကို သတိပေးရန် စာရင်းထုတ်ပေးသည်
        """
        summary = db.query(
            Inventory.blood_group,
            Inventory.rh_factor,
            func.sum(Inventory.quantity_ml).label("total_ml")
        ).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.status == "Available"
        ).group_by(
            Inventory.blood_group,
            Inventory.rh_factor
        ).having(func.sum(Inventory.quantity_ml) < threshold).all()

        warnings = []
        for item in summary:
            current_total = item.total_ml or 0
            warnings.append({
                "blood_type": f"{item.blood_group} {item.rh_factor}",
                "blood_group": item.blood_group,
                "rh_factor": item.rh_factor,
                "total_quantity": current_total,
                "warning_message": f"Low Stock Warning: {item.blood_group} {item.rh_factor} has dropped to {current_total} ml."
            })
            
        return warnings

    @staticmethod
    def _add_to_sync_queue(db: Session, inventory: Inventory, operation: str, delete: bool = False):
        data = {
            "blood_group": inventory.blood_group,
            "rh_factor": inventory.rh_factor,
            "quantity_ml": inventory.quantity_ml,
            "expiry_date": str(inventory.expiry_date),
            "status": inventory.status
        }
        sync_entry = SyncQueue(
            hospital_id=inventory.hospital_id,
            table_name="inventory",
            record_id=inventory.id,
            operation=operation,
            data=data,
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()