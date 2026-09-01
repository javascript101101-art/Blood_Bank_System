import uuid
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.inventory_schema import InventoryCreate, InventoryUpdate, InventorySplitRequest

class InventoryService:

    # ============================================
    # 🟢 Unit ID အလိုအလျောက် ဖန်တီးပေးသည့် Helper
    # ============================================
    @staticmethod
    def _generate_unit_id(component: str = None, parent_unit_id: str = None) -> str:
        """ Unit ID အလိုအလျောက် ဖန်တီးပေးသည့် Function """
        year = datetime.now().year
        if parent_unit_id and component:
            # ခွဲထုတ်လိုက်သော သွေးဆိုလျှင် မူလ ID အနောက်မှာ Component နာမည် တပ်ပေးမည် (ဥပမာ: UNIT-2026-ABCDEF-RBC)
            short_comp = "RBC" if component == "Red_Cells" else "FFP" if component == "Plasma" else "PLT" if component == "Platelets" else component
            return f"{parent_unit_id}-{short_comp}"
        else:
            # သွေးအသစ်ဆိုလျှင် အသစ်ထုတ်မည် (ဥပမာ: UNIT-2026-ABCDEF)
            random_hex = uuid.uuid4().hex[:6].upper()
            return f"UNIT-{year}-{random_hex}"
    
    @staticmethod
    def create_inventory(db: Session, inv_data: InventoryCreate, hospital_id: UUID) -> Inventory:
        today = datetime.now().date()
        calculated_expiry = inv_data.expiry_date
        storage_condition = None

        if inv_data.blood_component == "Red_Cells":
            calculated_expiry = today + timedelta(days=42)
            storage_condition = "+2°C to +6°C"
        elif inv_data.blood_component == "Plasma":
            calculated_expiry = today + timedelta(days=365)
            storage_condition = "-70°C"
        elif inv_data.blood_component == "Platelets":
            calculated_expiry = today + timedelta(days=5)
            storage_condition = "+22°C (Agitated)"
        elif inv_data.blood_component == "Whole_Blood":
            calculated_expiry = today + timedelta(days=35)
            storage_condition = "+2°C to +6°C"

        inventory = Inventory(
            hospital_id=hospital_id,
            donor_id=inv_data.donor_id,
            blood_group=inv_data.blood_group,
            rh_factor=inv_data.rh_factor,
            blood_component=inv_data.blood_component,
            quantity_ml=inv_data.quantity_ml,
            storage_condition=storage_condition,
            expiry_date=calculated_expiry,
            status=inv_data.status or "Available",
            # 🟢 Unit ID ထည့်သွင်းခြင်း
            unit_id=inv_data.unit_id or InventoryService._generate_unit_id()
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

        InventoryService._add_to_sync_queue(db, inventory, "INSERT")
        return inventory

    @staticmethod
    def get_inventories(db: Session, hospital_id: UUID) -> List[Inventory]:
        InventoryService._auto_expire_inventories(db, hospital_id)
        return db.query(Inventory).filter(Inventory.hospital_id == hospital_id).order_by(Inventory.created_at.desc()).all()

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
    # 🆕 Component Splitting Logic (သွေးခွဲထုတ်ခြင်း)
    # ============================================
    @staticmethod
    def split_inventory(db: Session, inv_id: UUID, hospital_id: UUID, split_data: InventorySplitRequest) -> Optional[List[Inventory]]:
        # ၁။ Quarantined ဖြစ်နေတဲ့ မူလသွေးအိတ်ကို ရှာပါမည်
        original_inv = db.query(Inventory).filter(
            Inventory.id == inv_id,
            Inventory.hospital_id == hospital_id,
            Inventory.status == "Quarantined"
        ).first()

        if not original_inv:
            return None # မတွေ့ပါက None ပြန်ပို့မည် (API မှ 400 Error ပြပေးပါမည်)

        # ၂။ မူလသွေးအိတ်ကို Processed (ခွဲထုတ်ပြီး) အခြေအနေသို့ ပြောင်းပါမည်
        original_inv.status = "Processed"
        InventoryService._add_to_sync_queue(db, original_inv, "UPDATE")

        new_components = []
        today = datetime.now().date()
        
        # 🟢 မူလ သွေးအိတ်နံပါတ်ကို ယူပါမည် (မရှိခဲ့လျှင် အသစ်ထုတ်မည်)
        parent_unit_id = original_inv.unit_id or InventoryService._generate_unit_id()

        # သွေးအစိတ်အပိုင်းများ အသစ်ဖန်တီးပေးမည့် Helper Function
        def _create_component(component_type, quantity, exp_days, storage):
            if quantity and quantity > 0:
                new_item = Inventory(
                    hospital_id=hospital_id,
                    donor_id=original_inv.donor_id,  # မူလလှူရှင်ကို ခြေရာခံနိုင်ရန် ပြန်ထည့်ပေးပါသည်
                    blood_group=original_inv.blood_group,
                    rh_factor=original_inv.rh_factor,
                    blood_component=component_type,
                    quantity_ml=quantity,
                    storage_condition=storage,
                    expiry_date=today + timedelta(days=exp_days),
                    status="Available", # ခွဲထုတ်ပြီးပါက အသင့်သုံးနိုင်ပြီဖြစ်သည်
                    # 🟢 Component အသစ်အတွက် Unit ID အသစ်ထုတ်ပေးခြင်း
                    unit_id=InventoryService._generate_unit_id(component_type, parent_unit_id)
                )
                db.add(new_item)
                new_components.append(new_item)

        # ၃။ Admin ရွေးချယ်လိုက်သော ပမာဏများအတိုင်း Row အသစ်များ ခွဲထုတ်ဖန်တီးပါမည်
        _create_component("Red_Cells", split_data.red_cells_ml, 42, "+2°C to +6°C")
        _create_component("Plasma", split_data.plasma_ml, 365, "-70°C")
        _create_component("Platelets", split_data.platelets_ml, 5, "+22°C (Agitated)")

        db.commit()

        # ၄။ Sync Queue ထဲသို့ အသစ်ရလာသော Component များကို ထည့်ပါမည်
        for item in new_components:
            db.refresh(item)
            InventoryService._add_to_sync_queue(db, item, "INSERT")

        return new_components

    # ============================================
    # Auto-Expire Logic
    # ============================================
    @staticmethod
    def _auto_expire_inventories(db: Session, hospital_id: UUID):
        today = datetime.now().date()
        expired_items = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.expiry_date < today,
            Inventory.status == "Available"
        ).all()

        for item in expired_items:
            item.status = "Expired"
            InventoryService._add_to_sync_queue(db, item, "UPDATE")
        
        if expired_items:
            db.commit()

    # ============================================
    # Low Stock Warnings Logic (Local Hospital)
    # ============================================
    @staticmethod
    def get_low_stock_warnings(db: Session, hospital_id: UUID, threshold: float = 500.0) -> List[dict]:
        summary = db.query(
            Inventory.blood_component,
            Inventory.blood_group,
            Inventory.rh_factor,
            func.sum(Inventory.quantity_ml).label("total_ml")
        ).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.status == "Available",
            Inventory.blood_component != "Whole_Blood"
        ).group_by(
            Inventory.blood_component,
            Inventory.blood_group,
            Inventory.rh_factor
        ).having(func.sum(Inventory.quantity_ml) < threshold).all()

        warnings = []
        for item in summary:
            current_total = item.total_ml or 0
            warnings.append({
                "blood_component": item.blood_component,
                "blood_type": f"{item.blood_group} {item.rh_factor}",
                "blood_group": item.blood_group,
                "rh_factor": item.rh_factor,
                "total_ml": current_total,  
                "total_quantity": current_total, 
                "warning_message": f"Low Stock Warning: {item.blood_component} ({item.blood_group} {item.rh_factor}) has dropped to {current_total} ml."
            })
            
        return warnings

    # ============================================
    # Sync Queue Helper
    # ============================================
    @staticmethod
    def _add_to_sync_queue(db: Session, inventory: Inventory, operation: str, delete: bool = False):
        data = {
            "blood_group": inventory.blood_group,
            "rh_factor": inventory.rh_factor,
            "quantity_ml": inventory.quantity_ml,
            "expiry_date": str(inventory.expiry_date),
            "status": inventory.status,
            "blood_component": inventory.blood_component,
            "storage_condition": inventory.storage_condition,
            "unit_id": inventory.unit_id # 🟢 Sync Data ထဲတွင် unit_id ကိုပါ ပေါင်းထည့်ပါသည်
        }
        if inventory.donor_id:
            data["donor_id"] = str(inventory.donor_id)
        if inventory.blood_request_id:
            data["blood_request_id"] = str(inventory.blood_request_id)

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