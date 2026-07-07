from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.hospital import Hospital
from app.models.sync import SyncQueue, SyncLog
from app.schemas.sync_schema import SyncQueueItem

class GlobalSyncService:
    
    @staticmethod
    def process_push(db: Session, hospital_id: UUID, items: List[SyncQueueItem]) -> Dict[str, Any]:
        success_ids = []
        failed_ids = []
        conflicts = []

        # Hospital ရှိမရှိ စစ်ပါ
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            for item in items:
                failed_ids.append(item.id)
            return {"success": success_ids, "failed": failed_ids, "conflicts": conflicts}

        for item in items:
            try:
                model_map = {
                    "donors": Donor,
                    "inventory": Inventory,
                    "blood_requests": BloodRequest
                }
                model = model_map.get(item.table_name)
                if not model:
                    failed_ids.append(item.id)
                    continue

                # ★★★ အရင်ဆုံး Sync Queue ထဲကို သိမ်းပါ ★★★
                sync_queue_entry = SyncQueue(
                    id=item.id,
                    hospital_id=hospital_id,
                    table_name=item.table_name,
                    record_id=item.record_id,
                    operation=item.operation,
                    data=item.data,
                    status="PENDING",
                    created_at=item.created_at
                )
                db.add(sync_queue_entry)
                db.flush()  # ID ကို ရရှိစေရန် (commit မလုပ်ဘဲ)

                # ပြီးမှ Record ကို စစ်ဆေးပါ
                existing_record = db.query(model).filter(model.id == item.record_id).first()

                if not existing_record:
                    # INSERT
                    new_record = model(**item.data, id=item.record_id, hospital_id=hospital_id)
                    db.add(new_record)
                    db.commit()
                    success_ids.append(item.id)
                    # အောင်မြင်ပြီးမှ Log ထည့်ပါ
                    GlobalSyncService._create_sync_log(db, item.id, "SUCCESS", "Inserted new record")
                    continue

                # UPDATE - Conflict Detection
                local_updated = item.data.get("_updated_at") or item.created_at
                global_updated = existing_record.updated_at if hasattr(existing_record, 'updated_at') else existing_record.created_at

                if global_updated and local_updated and global_updated > local_updated:
                    conflicts.append({
                        "id": str(item.id),
                        "record_id": str(item.record_id),
                        "table_name": item.table_name,
                        "global_data": {c.name: getattr(existing_record, c.name) for c in model.__table__.columns},
                        "local_data": item.data,
                        "message": "Global data is newer than local data"
                    })
                    db.commit()
                    GlobalSyncService._create_sync_log(db, item.id, "CONFLICT_DETECTED", conflict_details={
                        "global_updated": global_updated.isoformat(),
                        "local_updated": local_updated.isoformat()
                    })
                    continue

                # UPDATE: Local data က ပိုသစ်ရင်
                for key, value in item.data.items():
                    if hasattr(existing_record, key) and key not in ["id", "hospital_id", "created_at"]:
                        setattr(existing_record, key, value)
                existing_record.hospital_id = hospital_id
                db.commit()
                success_ids.append(item.id)
                GlobalSyncService._create_sync_log(db, item.id, "SUCCESS", "Updated record")

            except Exception as e:
                db.rollback()
                failed_ids.append(item.id)
                try:
                    GlobalSyncService._create_sync_log(db, item.id, "FAILED", str(e))
                except Exception as log_error:
                    print(f"Error creating sync log: {log_error}")

        return {
            "success": success_ids,
            "failed": failed_ids,
            "conflicts": conflicts
        }

    @staticmethod
    def _create_sync_log(db: Session, sync_queue_id: UUID, status: str, error_message: str = None, conflict_details: dict = None):
        try:
            log = SyncLog(
                sync_queue_id=sync_queue_id,
                status=status,
                error_message=error_message,
                conflict_details=conflict_details
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error creating sync log: {e}")