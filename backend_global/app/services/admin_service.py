from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List  # ★ ဒီ line ကို ထည့်ပါ
from app.models.hospital import Hospital
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.sync import SyncLog
from app.schemas.admin_schema import HospitalStats, GlobalStats, SyncLogEntry

class AdminService:
    @staticmethod
    def get_global_stats(db: Session) -> GlobalStats:
        # Total counts
        total_donors = db.query(func.count(Donor.id)).scalar() or 0
        total_inventory = db.query(func.count(Inventory.id)).scalar() or 0
        total_requests = db.query(func.count(BloodRequest.id)).scalar() or 0
        total_hospitals = db.query(func.count(Hospital.id)).scalar() or 0

        # Per hospital stats
        hospitals = db.query(Hospital).all()
        hospital_stats = []
        for h in hospitals:
            donor_count = db.query(func.count(Donor.id)).filter(Donor.hospital_id == h.id).scalar() or 0
            inventory_count = db.query(func.count(Inventory.id)).filter(Inventory.hospital_id == h.id).scalar() or 0
            request_count = db.query(func.count(BloodRequest.id)).filter(BloodRequest.hospital_id == h.id).scalar() or 0
            
            hospital_stats.append(HospitalStats(
                hospital_id=h.id,
                name=h.name,
                location=h.location,
                donor_count=donor_count,
                inventory_count=inventory_count,
                request_count=request_count
            ))

        return GlobalStats(
            total_donors=total_donors,
            total_inventory=total_inventory,
            total_requests=total_requests,
            total_hospitals=total_hospitals,
            hospitals=hospital_stats
        )

    @staticmethod
    def get_sync_logs(db: Session, limit: int = 50) -> List[SyncLogEntry]:
        logs = db.query(SyncLog).order_by(SyncLog.sync_timestamp.desc()).limit(limit).all()
        return [
            SyncLogEntry(
                id=log.id,
                status=log.status,
                error_message=log.error_message,
                sync_timestamp=log.sync_timestamp.isoformat()
            ) for log in logs
        ]