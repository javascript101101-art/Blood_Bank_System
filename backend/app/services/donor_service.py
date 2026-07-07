from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.models.donor import Donor
from app.models.sync import SyncQueue
from app.schemas.donor_schema import DonorCreate, DonorUpdate
import json

class DonorService:
    @staticmethod
    def create_donor(db: Session, donor_data: DonorCreate, hospital_id: UUID) -> Donor:
        donor = Donor(**donor_data.model_dump(), hospital_id=hospital_id)
        db.add(donor)
        db.commit()
        db.refresh(donor)
        
        # Sync Queue ထဲထည့်ပါ
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
        
        # Sync Queue ထဲထည့်ပါ
        DonorService._add_to_sync_queue(db, donor, "UPDATE")
        return donor

    @staticmethod
    def delete_donor(db: Session, donor_id: UUID, hospital_id: UUID) -> bool:
        donor = DonorService.get_donor(db, donor_id, hospital_id)
        if not donor:
            return False
        
        # Sync Queue ထဲထည့်ပါ (DELETE)
        DonorService._add_to_sync_queue(db, donor, "DELETE", delete=True)
        
        db.delete(donor)
        db.commit()
        return True

    @staticmethod
    def _add_to_sync_queue(db: Session, donor: Donor, operation: str, delete: bool = False):
        data = {
            "name": donor.name,
            "blood_group": donor.blood_group,
            "rh_factor": donor.rh_factor,
            "contact_phone": donor.contact_phone
        }
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