from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.inventory_schema import InventoryCreate, InventoryUpdate

class InventoryService:
    @staticmethod
    def create_inventory(db: Session, inv_data: InventoryCreate, hospital_id: UUID) -> Inventory:
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