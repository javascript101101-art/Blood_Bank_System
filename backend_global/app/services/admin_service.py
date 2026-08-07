from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any  # 🟢 Dict, Any ကိုပါ ထပ်ထည့်ထားပါသည်
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

    # ============================================
    # 🆕 Low Stock Warning Logic
    # ============================================
    @staticmethod
    def get_low_stock_warnings(db: Session, threshold: int = 100) -> List[Dict[str, Any]]:
        """
        Global အတွက် ဆေးရုံအားလုံးရှိ သွေးအမျိုးအစားအလိုက် စုစုပေါင်း ပမာဏကို တွက်ပြီး 
        သတ်မှတ်ထားတဲ့ threshold (ဥပမာ - 100) အောက် ရောက်နေရင် Warning ပြန်ပေးမည်
        """
        low_stock_alerts = []
        
        # သွေးအမျိုးအစား (A, B, O) နှင့် RH Factor (+, -) အလိုက် Group ဖွဲ့ပြီး ပေါင်းမည်
        results = db.query(
            Inventory.blood_group,
            Inventory.rh_factor,
            func.sum(Inventory.quantity_ml).label('total_quantity') # 💡 မှတ်ချက်: quantity_ml အစား quantity_units သုံးထားလျှင် ပြောင်းပေးပါ
        ).filter(
            Inventory.status == "Available" # Available ဖြစ်နေတဲ့ သွေးတွေကိုပဲ တွက်မယ်
        ).group_by(
            Inventory.blood_group,
            Inventory.rh_factor
        ).all()

        for bg, rh, total in results:
            current_total = total if total else 0
            if current_total < threshold:
                low_stock_alerts.append({
                    "blood_type": f"{bg} {rh}", # ဥပမာ: "O Positive"
                    "blood_group": bg,
                    "rh_factor": rh,
                    "total_quantity": current_total,
                    "warning_message": f"Low Stock Warning: Global inventory for {bg} {rh} has dropped to {current_total}."
                })
                
        return low_stock_alerts