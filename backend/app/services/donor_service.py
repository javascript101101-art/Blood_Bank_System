from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.donor_schema import DonorCreate, DonorUpdate

class DonorService:
    
    @staticmethod
    def create_donor(db: Session, donor_data: DonorCreate, hospital_id: UUID) -> Donor:
        donor = Donor(**donor_data.model_dump(), hospital_id=hospital_id)
        db.add(donor)
        db.commit()
        db.refresh(donor)

        # ✅ ဒီမှာ donor.donation_quantity ကို သုံးတယ်
        DonorService._update_inventory_on_donation(db, donor, hospital_id)
        DonorService._add_to_sync_queue(db, donor, "INSERT")
        return donor

    @staticmethod
    def get_donors(db: Session, hospital_id: UUID) -> List[Donor]:
        return db.query(Donor).filter(Donor.hospital_id == hospital_id).all()

    @staticmethod
    def get_donor(db: Session, donor_id: UUID, hospital_id: UUID) -> Optional[Donor]:
        return db.query(Donor).filter(
            Donor.id == donor_id,
            Donor.hospital_id == hospital_id
        ).first()

    @staticmethod
    def update_donor(db: Session, donor_id: UUID, hospital_id: UUID, donor_data: DonorUpdate) -> Optional[Donor]:
        donor = DonorService.get_donor(db, donor_id, hospital_id)
        if not donor:
            return None
        
        for key, value in donor_data.model_dump(exclude_unset=True).items():
            setattr(donor, key, value)
        
        db.commit()
        db.refresh(donor)
        DonorService._add_to_sync_queue(db, donor, "UPDATE")
        return donor

    @staticmethod
    def delete_donor(db: Session, donor_id: UUID, hospital_id: UUID) -> bool:
        donor = DonorService.get_donor(db, donor_id, hospital_id)
        if not donor:
            return False
        
        DonorService._add_to_sync_queue(db, donor, "DELETE", delete=True)
        db.delete(donor)
        db.commit()
        return True

    # ============================================
    # 🆕 Inventory Update on Donation
    # ============================================
    @staticmethod
    def _update_inventory_on_donation(db: Session, donor: Donor, hospital_id: UUID):
        # ✅ ဒီမှာ သေချာစစ်ပါ - donor.donation_quantity ကို သုံးတယ်
        donation_quantity = donor.donation_quantity
        print(f"✅ Donation Quantity from donor: {donation_quantity}")  # Debugging

        inventory_item = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.blood_group == donor.blood_group,
            Inventory.rh_factor == donor.rh_factor
        ).first()

        if inventory_item:
            inventory_item.quantity_ml += donation_quantity
        else:
            inventory_item = Inventory(
                hospital_id=hospital_id,
                blood_group=donor.blood_group,
                rh_factor=donor.rh_factor,
                quantity_ml=donation_quantity,
                expiry_date=datetime.now() + timedelta(days=30),
                status="Available"
            )
            db.add(inventory_item)

        db.commit()
        db.refresh(inventory_item)

        # Sync Queue ထဲထည့်ပါ
        inv_sync_data = {
            "blood_group": inventory_item.blood_group,
            "rh_factor": inventory_item.rh_factor,
            "quantity_ml": inventory_item.quantity_ml,
            "expiry_date": str(inventory_item.expiry_date),
            "status": inventory_item.status
        }
        inv_sync_entry = SyncQueue(
            hospital_id=hospital_id,
            table_name="inventory",
            record_id=inventory_item.id,
            operation="UPDATE",
            data=inv_sync_data,
            status="PENDING"
        )
        db.add(inv_sync_entry)
        db.commit()

    # ============================================
    # Sync Queue Helper
    # ============================================
    @staticmethod
    def _add_to_sync_queue(db: Session, donor: Donor, operation: str, delete: bool = False):
        data = {
            "name": donor.name,
            "blood_group": donor.blood_group,
            "rh_factor": donor.rh_factor,
            "contact_phone": donor.contact_phone,
            "donation_quantity": donor.donation_quantity
        }
        if donor.dob:
            data["dob"] = donor.dob.isoformat()
        if donor.email:
            data["email"] = donor.email
        
        sync_entry = SyncQueue(
            hospital_id=donor.hospital_id,
            table_name="donors",
            record_id=donor.id,
            operation=operation,
            data=data,
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()