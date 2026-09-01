import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from app.models.global_inventory import GlobalInventory
from app.models.global_blood_request import GlobalBloodRequest
from app.schemas.global_inventory_schema import GlobalInventorySummary, DeliverBloodRequest

class GlobalInventoryService:

    # ============================================
    # 🟢 Global အတွက် Unit ID အလိုအလျောက် ဖန်တီးပေးသည့် Helper
    # ============================================
    @staticmethod
    def _generate_unit_id(component: str = None) -> str:
        """ Unit ID အလိုအလျောက် ဖန်တီးပေးသည့် Function """
        year = datetime.now().year
        random_hex = uuid.uuid4().hex[:6].upper()
        short_comp = "RBC" if component == "Red_Cells" else "FFP" if component == "Plasma" else "PLT" if component == "Platelets" else "WB"
        return f"GLB-{year}-{random_hex}-{short_comp}"

    @staticmethod
    def add_blood(
        db: Session,
        blood_component: str,
        blood_group: str,
        rh_factor: str,
        quantity_ml: int,
        source_hospital_id: Optional[UUID] = None,
        source_request_id: Optional[UUID] = None,
        unit_id: Optional[str] = None, 
        supplier: Optional[str] = None,       
        expiry_date: Optional[datetime] = None, 
        number_of_units: int = 1              
    ) -> List[GlobalInventory]:
        """Global Inventory မှာ Blood ထည့်မယ် (Bulk Insert အပါအဝင်)"""
        
        added_inventories = []
        
        for i in range(number_of_units):
            current_unit_id = unit_id if (unit_id and number_of_units == 1) else GlobalInventoryService._generate_unit_id(blood_component)

            inventory = GlobalInventory(
                unit_id=current_unit_id,
                blood_component=blood_component,
                blood_group=blood_group,
                rh_factor=rh_factor,
                quantity_ml=quantity_ml,
                supplier=supplier,          
                expiry_date=expiry_date,    
                status="Available",
                source_hospital_id=source_hospital_id,
                source_request_id=source_request_id
            )
            db.add(inventory)
            added_inventories.append(inventory)
        
        db.commit()
        
        for inv in added_inventories:
            db.refresh(inv)
            
        return added_inventories 

    # ============================================
    # 🟢 [အသစ်] Unit ID များ ပြန်ထုတ်ပေးမည့် remove_blood
    # ============================================
    @staticmethod
    def remove_blood(
        db: Session,
        blood_component: str, 
        blood_group: str,
        rh_factor: str,
        quantity_ml: int
    ) -> List[str]: # 🟢 Return type ကို List[str] အဖြစ် ပြောင်းထားပါသည်
        """Global Inventory ကနေ Blood ဖြုတ်မယ် (Deliver လုပ်တဲ့အခါ)"""
        # FIFO (First In First Out) - အဟောင်းဆုံးကနေ စဖြုတ်
        inventories = db.query(GlobalInventory).filter(
            GlobalInventory.blood_component == blood_component, 
            GlobalInventory.blood_group == blood_group,
            GlobalInventory.rh_factor == rh_factor,
            GlobalInventory.quantity_ml > 0,
            GlobalInventory.status == "Available" 
        ).order_by(GlobalInventory.created_at.asc()).all()

        # 🟢 အရင်ဆုံး Stock လောက်/မလောက် စစ်ပါမည်
        total_available = sum(inv.quantity_ml for inv in inventories)
        if total_available < quantity_ml:
            return [] # သွေးမလောက်ပါက Array အလွတ် ပြန်ပေးမည် (Error တက်စေရန်)

        remaining = quantity_ml
        used_unit_ids = [] # 🟢 အသုံးပြုလိုက်သော Unit ID များကို သိမ်းဆည်းရန်

        for inv in inventories:
            if remaining <= 0:
                break
            
            # 🟢 သုံးလိုက်သော သွေးအိတ်၏ Unit ID ကို စာရင်းသွင်းမည်
            if inv.unit_id and inv.unit_id not in used_unit_ids:
                used_unit_ids.append(inv.unit_id)

            if inv.quantity_ml <= remaining:
                remaining -= inv.quantity_ml
                inv.quantity_ml = 0
                inv.status = "Used" 
            else:
                inv.quantity_ml -= remaining
                remaining = 0

        db.commit()
        
        # 🟢 အသုံးပြုလိုက်သော Unit ID စာရင်း (ဥပမာ - ["GLB-123", "GLB-456"]) ကို ပြန်ထုတ်ပေးပါမည်
        return used_unit_ids

    @staticmethod
    def get_total_by_blood_type(db: Session, blood_component: str, blood_group: str, rh_factor: str) -> int:
        total = db.query(func.sum(GlobalInventory.quantity_ml)).filter(
            GlobalInventory.blood_component == blood_component, 
            GlobalInventory.blood_group == blood_group,
            GlobalInventory.rh_factor == rh_factor,
            GlobalInventory.status == "Available"
        ).scalar()
        return total or 0

    @staticmethod
    def get_summary(db: Session) -> List[GlobalInventorySummary]:
        results = db.query(
            GlobalInventory.blood_component, 
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor,
            func.sum(GlobalInventory.quantity_ml).label('total_ml')
        ).filter(
            GlobalInventory.quantity_ml > 0,
            GlobalInventory.status == "Available",
            GlobalInventory.blood_component != "Whole_Blood" 
        ).group_by(
            GlobalInventory.blood_component, 
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor
        ).order_by(
            GlobalInventory.blood_component,
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor
        ).all()

        return [
            GlobalInventorySummary(
                blood_component=row.blood_component, 
                blood_group=row.blood_group,
                rh_factor=row.rh_factor,
                total_ml=row.total_ml
            )
            for row in results
        ]

    @staticmethod
    def get_all_inventory(db: Session) -> List[GlobalInventory]:
        return db.query(GlobalInventory).filter(
            GlobalInventory.quantity_ml > 0
        ).order_by(GlobalInventory.created_at.desc()).all()

    @staticmethod
    def check_stock(db: Session, blood_component: str, blood_group: str, rh_factor: str, quantity_ml: int) -> bool:
        total = GlobalInventoryService.get_total_by_blood_type(db, blood_component, blood_group, rh_factor)
        return total >= quantity_ml