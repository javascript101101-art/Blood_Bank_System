from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from app.models.global_inventory import GlobalInventory
from app.models.global_blood_request import GlobalBloodRequest
from app.schemas.global_inventory_schema import GlobalInventorySummary, DeliverBloodRequest


class GlobalInventoryService:

    @staticmethod
    def add_blood(
        db: Session,
        blood_group: str,
        rh_factor: str,
        quantity_ml: int,
        source_hospital_id: UUID,
        source_request_id: UUID
    ) -> GlobalInventory:
        """Global Inventory မှာ Blood ထည့်မယ် (Supplier က Fulfill လုပ်တဲ့အခါ)"""
        inventory = GlobalInventory(
            blood_group=blood_group,
            rh_factor=rh_factor,
            quantity_ml=quantity_ml,
            source_hospital_id=source_hospital_id,
            source_request_id=source_request_id
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return inventory

    @staticmethod
    def remove_blood(
        db: Session,
        blood_group: str,
        rh_factor: str,
        quantity_ml: int
    ) -> bool:
        """Global Inventory ကနေ Blood ဖြုတ်မယ် (Deliver လုပ်တဲ့အခါ)"""
        # FIFO (First In First Out) - အဟောင်းဆုံးကနေ စဖြုတ်
        inventories = db.query(GlobalInventory).filter(
            GlobalInventory.blood_group == blood_group,
            GlobalInventory.rh_factor == rh_factor,
            GlobalInventory.quantity_ml > 0
        ).order_by(GlobalInventory.created_at.asc()).all()

        remaining = quantity_ml
        for inv in inventories:
            if remaining <= 0:
                break
            if inv.quantity_ml <= remaining:
                remaining -= inv.quantity_ml
                inv.quantity_ml = 0
            else:
                inv.quantity_ml -= remaining
                remaining = 0

        db.commit()
        return remaining == 0

    @staticmethod
    def get_total_by_blood_type(db: Session, blood_group: str, rh_factor: str) -> int:
        """Global Inventory မှာ စုစုပေါင်း ဘယ်လောက်ရှိလဲ"""
        total = db.query(func.sum(GlobalInventory.quantity_ml)).filter(
            GlobalInventory.blood_group == blood_group,
            GlobalInventory.rh_factor == rh_factor
        ).scalar()
        return total or 0

    @staticmethod
    def get_summary(db: Session) -> List[GlobalInventorySummary]:
        """Blood type အလိုက် စုစုပေါင်း Summary"""
        results = db.query(
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor,
            func.sum(GlobalInventory.quantity_ml).label('total_ml')
        ).filter(
            GlobalInventory.quantity_ml > 0
        ).group_by(
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor
        ).order_by(
            GlobalInventory.blood_group,
            GlobalInventory.rh_factor
        ).all()

        return [
            GlobalInventorySummary(
                blood_group=row.blood_group,
                rh_factor=row.rh_factor,
                total_ml=row.total_ml
            )
            for row in results
        ]

    @staticmethod
    def get_all_inventory(db: Session) -> List[GlobalInventory]:
        """Global Inventory အကုန်"""
        return db.query(GlobalInventory).filter(
            GlobalInventory.quantity_ml > 0
        ).order_by(GlobalInventory.created_at.desc()).all()

    @staticmethod
    def check_stock(db: Session, blood_group: str, rh_factor: str, quantity_ml: int) -> bool:
        """Stock ရှိ/မရှိ စစ်ပါ"""
        total = GlobalInventoryService.get_total_by_blood_type(db, blood_group, rh_factor)
        return total >= quantity_ml
