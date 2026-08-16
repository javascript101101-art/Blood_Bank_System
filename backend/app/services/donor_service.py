from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.donor_schema import DonorCreate, DonorUpdate

class DonorService:
    
    @staticmethod
    def create_donor(db: Session, donor_data: DonorCreate, hospital_id: UUID) -> Donor:
        # 🟢 ၁။ Validation: (၉၀) ရက်ပြည့်/မပြည့် စစ်ဆေးခြင်း
        if donor_data.last_donation_date:
            days_since_last = (datetime.now().date() - donor_data.last_donation_date).days
            if days_since_last < 90:
                raise HTTPException(status_code=400, detail=f"သွေးလှူရန် ရက်မပြည့်သေးပါ။ နောက်ဆုံးလှူခဲ့သည့်ရက်မှ {days_since_last} ရက်သာ ရှိသေးသည်။")

        # 🟢 ၂။ Validation: ကျန်းမာရေး အခြေအနေ စစ်ဆေးခြင်း
        if donor_data.hemoglobin_level and donor_data.hemoglobin_level < 12.0:
            raise HTTPException(status_code=400, detail="Haemoglobin (သွေးအား) နည်းနေသဖြင့် သွေးလှူရန် မသင့်တော်ပါ။")

        donor = Donor(**donor_data.model_dump(), hospital_id=hospital_id)
        db.add(donor)
        db.commit()
        db.refresh(donor)

        # 🟢 ၃။ Inventory သို့ သွေးအိတ်စိမ်း (Whole Blood) အဖြစ် မှတ်တမ်းတင်ခြင်း (Lab မစစ်ရသေးပါ)
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
    # 🆕 Get Donor History (Traceability Logic)
    # ============================================
    @staticmethod
    def get_donor_history(db: Session, donor_id: UUID, hospital_id: UUID) -> List[Inventory]:
        """အလှူရှင်တစ်ဦးချင်းစီ၏ သွေးလှူဒါန်းမှု မှတ်တမ်းနှင့် ခွဲထုတ်ထားသော သွေးအစိတ်အပိုင်းများကို ရယူရန်"""
        return db.query(Inventory).filter(
            Inventory.donor_id == donor_id,
            Inventory.hospital_id == hospital_id
        ).order_by(Inventory.created_at.desc()).all()

    # ============================================
    # Inventory Update on Donation (Modified for New Workflow)
    # ============================================
    @staticmethod
    def _update_inventory_on_donation(db: Session, donor: Donor, hospital_id: UUID):
        donation_quantity = donor.donation_quantity
        print(f"✅ Storing Collected Blood from donor: {donor.id}, Qty: {donation_quantity}ml")

        # 🟢 ၄။ ရှိပြီးသားထဲ သွားမပေါင်းဘဲ، ဒီအလှူရှင်အတွက် "Quarantined" အနေနဲ့ သီးသန့် Record အသစ်ဆောက်ပါမည်
        inventory_item = Inventory(
            hospital_id=hospital_id,
            donor_id=donor.id,                          # သွေးလှူရှင်ကို ခြေရာခံရန်
            blood_group=donor.blood_group,
            rh_factor=donor.rh_factor,
            blood_component="Whole_Blood",              # မခွဲရသေးသော သွေးအိတ်စိမ်း
            quantity_ml=donation_quantity,
            storage_condition="+2°C to +6°C (Temp)",
            expiry_date=datetime.now() + timedelta(days=35), # Standard whole blood expiry
            status="Quarantined"                        # Lab စစ်ဆေးရန် စောင့်ဆိုင်းနေဆဲဖြစ်ကြောင်း
        )
        db.add(inventory_item)
        db.commit()
        db.refresh(inventory_item)

        # Sync Queue ထဲထည့်ပါ
        inv_sync_data = {
            "donor_id": str(inventory_item.donor_id),
            "blood_group": inventory_item.blood_group,
            "rh_factor": inventory_item.rh_factor,
            "blood_component": inventory_item.blood_component,
            "quantity_ml": inventory_item.quantity_ml,
            "expiry_date": str(inventory_item.expiry_date),
            "status": inventory_item.status
        }
        inv_sync_entry = SyncQueue(
            hospital_id=hospital_id,
            table_name="inventory",
            record_id=inventory_item.id,
            operation="INSERT", # အသစ်ဆောက်တာဖြစ်လို့ INSERT သုံးရပါမည်
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
            "donation_quantity": donor.donation_quantity,
            "hemoglobin_level": donor.hemoglobin_level,     # 🟢 အသစ်ထည့်ထားသော fields
            "temperature": donor.temperature,               # 🟢 အသစ်ထည့်ထားသော fields
            "blood_pressure": donor.blood_pressure          # 🟢 အသစ်ထည့်ထားသော fields
        }
        if donor.dob:
            data["dob"] = donor.dob.isoformat()
        if donor.email:
            data["email"] = donor.email
        if donor.last_donation_date:
            data["last_donation_date"] = donor.last_donation_date.isoformat()
        
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