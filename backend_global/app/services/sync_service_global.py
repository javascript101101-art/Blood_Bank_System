from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.global_blood_request import GlobalBloodRequest
from app.models.hospital import Hospital
from app.models.sync import SyncQueue, SyncLog
from app.schemas.sync_schema import SyncQueueItem

class GlobalSyncService:
    
    @staticmethod
    def process_push(db: Session, hospital_id: UUID, items: List[SyncQueueItem]) -> Dict[str, Any]:
        print(f"🟢 Global Sync Received - Hospital ID: {hospital_id}")
        print(f"🟢 Items count: {len(items)}")
        
        for item in items:
            print(f"🟢 Item: {item.table_name} - {item.operation} - {item.record_id}")
        
        success_ids = []
        failed_ids = []
        conflicts = []

        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            print(f"❌ Hospital not found: {hospital_id}")
            for item in items:
                failed_ids.append(item.id)
            return {"success": success_ids, "failed": failed_ids, "conflicts": conflicts}

        for item in items:
            try:
                model_map = {
                    "donors": Donor,
                    "inventory": Inventory,
                    "blood_requests": BloodRequest,
                    "global_blood_requests": GlobalBloodRequest
                }
                model = model_map.get(item.table_name)
                if not model:
                    print(f"❌ Unknown table: {item.table_name}")
                    failed_ids.append(item.id)
                    continue

                print(f"🟢 Processing: {item.table_name} - ID: {item.record_id}")
                print(f"🟢 Data: {item.data}")

                # Create sync queue entry in global
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
                db.flush()

                existing_record = db.query(model).filter(model.id == item.record_id).first()

                if not existing_record:
                    # INSERT - Create new record
                    item_data = {k: v for k, v in item.data.items() if k != 'id'}
                    
                    # 🆕 Check required fields for Donor
                    if model == Donor:
                        # Ensure rh_factor exists
                        if 'rh_factor' not in item_data:
                            print(f"⚠️ Missing rh_factor, using default 'Positive'")
                            item_data['rh_factor'] = 'Positive'
                        # Ensure blood_group exists
                        if 'blood_group' not in item_data:
                            print(f"⚠️ Missing blood_group, using default 'O'")
                            item_data['blood_group'] = 'O'
                    
                    # Special handling for GlobalBloodRequest (no hospital_id)
                    if model == GlobalBloodRequest:
                        new_record = model(**item_data, id=item.record_id)
                    else:
                        new_record = model(**item_data, id=item.record_id, hospital_id=hospital_id)
                    
                    db.add(new_record)
                    db.commit()
                    success_ids.append(item.id)
                    print(f"✅ Inserted: {item.table_name} - {item.record_id}")
                    GlobalSyncService._create_sync_log(db, item.id, "SUCCESS", "Inserted new record")
                    continue

                # UPDATE
                local_updated = item.data.get("_updated_at") or item.created_at
                global_updated = existing_record.updated_at if hasattr(existing_record, 'updated_at') else existing_record.created_at

                if global_updated and local_updated and global_updated > local_updated:
                    print(f"⚠️ Conflict: {item.table_name} - {item.record_id}")
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

                for key, value in item.data.items():
                    if hasattr(existing_record, key) and key not in ["id", "hospital_id", "created_at"]:
                        setattr(existing_record, key, value)
                
                if model != GlobalBloodRequest:
                    existing_record.hospital_id = hospital_id
                
                db.commit()
                success_ids.append(item.id)
                print(f"✅ Updated: {item.table_name} - {item.record_id}")
                GlobalSyncService._create_sync_log(db, item.id, "SUCCESS", "Updated record")

            except Exception as e:
                db.rollback()
                failed_ids.append(item.id)
                print(f"❌ Error: {item.table_name} - {item.record_id}: {str(e)}")
                try:
                    GlobalSyncService._create_sync_log(db, item.id, "FAILED", str(e))
                except Exception as log_error:
                    print(f"❌ Log error: {log_error}")

        print(f"🟢 Sync completed - Success: {len(success_ids)}, Failed: {len(failed_ids)}, Conflicts: {len(conflicts)}")
        
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
            print(f"❌ Log error: {e}")