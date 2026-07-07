from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any
import httpx
from app.models.sync import SyncQueue, SyncLog
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.config import settings

class SyncService:
    # Global Server URL (POC အတွက်)
    GLOBAL_SYNC_URL = "http://localhost:8001/api/v1/sync/push"
    GLOBAL_LOGIN_URL = "http://localhost:8001/api/v1/auth/login"
    GLOBAL_USERNAME = "global_admin"
    GLOBAL_PASSWORD = "admin123"

    @staticmethod
    def _get_global_token() -> str:
        """Global Server မှ Access Token ကို ရယူပါ"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    SyncService.GLOBAL_LOGIN_URL,
                    data={
                        "username": SyncService.GLOBAL_USERNAME,
                        "password": SyncService.GLOBAL_PASSWORD
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                token_data = response.json()
                return token_data.get("access_token")
        except Exception as e:
            print(f"Failed to get global token: {e}")
            return None

    @staticmethod
    def get_pending_items(db: Session, hospital_id: UUID) -> List[SyncQueue]:
        """PENDING Status ရှိတဲ့ Sync Queue Items တွေကို ဆွဲယူပါ"""
        return db.query(SyncQueue).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "PENDING"
        ).order_by(SyncQueue.created_at).all()

    @staticmethod
    def push_to_global(db: Session, hospital_id: UUID) -> Dict[str, Any]:
        """Local Data ကို Global Server ဆီ Push လုပ်ပါ"""
        pending_items = SyncService.get_pending_items(db, hospital_id)
        if not pending_items:
            return {"message": "No pending items to sync", "synced": 0, "failed": 0}

        # Prepare payload
        payload = {
            "hospital_id": str(hospital_id),
            "items": [
                {
                    "id": str(item.id),
                    "table_name": item.table_name,
                    "record_id": str(item.record_id),
                    "operation": item.operation,
                    "data": item.data,
                    "status": item.status,
                    "created_at": item.created_at.isoformat()
                }
                for item in pending_items
            ]
        }

        # Get Global Token
        token = SyncService._get_global_token()
        if not token:
            return {"message": "Failed to authenticate with Global Server", "synced": 0, "failed": len(pending_items)}

        try:
            # Send to Global Server with Authorization
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    SyncService.GLOBAL_SYNC_URL,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}"
                    }
                )
                response.raise_for_status()
                result = response.json()

            # Update local sync queue status based on response
            synced_ids = result.get("success", [])
            failed_ids = result.get("failed", [])
            conflicts = result.get("conflicts", [])

            # Update status for synced items
            for item in pending_items:
                if str(item.id) in synced_ids:
                    item.status = "SYNCED"
                    SyncService._create_sync_log(db, item.id, "SUCCESS")
                elif str(item.id) in failed_ids:
                    item.status = "FAILED"
                    item.retry_count += 1
                    SyncService._create_sync_log(db, item.id, "FAILED", "Failed on global server")
                elif any(str(item.id) == c.get("id") for c in conflicts):
                    item.status = "CONFLICT"
                    conflict_detail = next(c for c in conflicts if str(item.id) == c.get("id"))
                    SyncService._create_sync_log(db, item.id, "CONFLICT_DETECTED", conflict_details=conflict_detail)
                    # Auto-resolve conflict: Overwrite with global data (Last-Write-Wins)
                    SyncService._resolve_conflict(db, item, conflict_detail)

            db.commit()
            return {
                "message": "Sync completed",
                "synced": len(synced_ids),
                "failed": len(failed_ids),
                "conflicts": len(conflicts)
            }

        except httpx.RequestError as e:
            # Network error - keep as PENDING for retry
            return {"message": f"Network error: {str(e)}", "synced": 0, "failed": len(pending_items)}
        except Exception as e:
            db.rollback()
            return {"message": f"Sync error: {str(e)}", "synced": 0, "failed": len(pending_items)}

    @staticmethod
    def _resolve_conflict(db: Session, item: SyncQueue, conflict_detail: dict):
        """Last-Write-Wins: Global data က Local ကို ပြန်ရေးပါ"""
        table_name = item.table_name
        record_id = item.record_id
        global_data = conflict_detail.get("global_data", {})

        if table_name == "donors":
            donor = db.query(Donor).filter(Donor.id == record_id).first()
            if donor:
                for key, value in global_data.items():
                    if hasattr(donor, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        setattr(donor, key, value)
                db.commit()
        elif table_name == "inventory":
            inventory = db.query(Inventory).filter(Inventory.id == record_id).first()
            if inventory:
                for key, value in global_data.items():
                    if hasattr(inventory, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        setattr(inventory, key, value)
                db.commit()
        elif table_name == "blood_requests":
            request = db.query(BloodRequest).filter(BloodRequest.id == record_id).first()
            if request:
                for key, value in global_data.items():
                    if hasattr(request, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        setattr(request, key, value)
                db.commit()

    @staticmethod
    def _create_sync_log(db: Session, sync_queue_id: UUID, status: str, error_message: str = None, conflict_details: dict = None):
        log = SyncLog(
            sync_queue_id=sync_queue_id,
            status=status,
            error_message=error_message,
            conflict_details=conflict_details
        )
        db.add(log)

    @staticmethod
    def get_sync_status(db: Session, hospital_id: UUID) -> dict:
        """Sync Status ကို ပြန်ပေးပါ"""
        pending = db.query(func.count(SyncQueue.id)).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "PENDING"
        ).scalar() or 0

        synced = db.query(func.count(SyncQueue.id)).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "SYNCED"
        ).scalar() or 0

        failed = db.query(func.count(SyncQueue.id)).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "FAILED"
        ).scalar() or 0

        conflict = db.query(func.count(SyncQueue.id)).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "CONFLICT"
        ).scalar() or 0

        # last_sync_at ကို ရှာပါ (အောင်မြင်ဆုံး sync log ကို သုံးမယ်)
        last_sync = db.query(SyncLog.sync_timestamp).filter(
            SyncLog.status == "SUCCESS"
        ).order_by(SyncLog.sync_timestamp.desc()).first()

        return {
            "pending_count": pending,
            "synced_count": synced,
            "failed_count": failed,
            "conflict_count": conflict,
            "last_sync_at": last_sync[0] if last_sync else None
        }