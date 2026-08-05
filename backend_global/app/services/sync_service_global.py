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
            # SyncQueue ကို အရင် Save (Commit) လုပ်မည်
            try:
                item_data_clean = {k: v for k, v in item.data.items() if k != '_updated_at'}
                
                sync_queue_entry = SyncQueue(
                    id=item.id,
                    hospital_id=hospital_id,
                    table_name=item.table_name,
                    record_id=item.record_id,
                    operation=item.operation,
                    data=item_data_clean,
                    status="PENDING",
                    created_at=item.created_at
                )
                db.add(sync_queue_entry)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"❌ Failed to save SyncQueue {item.id}: {e}")
                failed_ids.append(item.id)
                continue

            # Main Logic
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

                existing_record = db.query(model).filter(model.id == item.record_id).first()

                if not existing_record:
                    # INSERT - Create new record
                    item_data = {k: v for k, v in item.data.items() if k not in ['id', '_updated_at']}
                    
                    if model == Donor:
                        if 'rh_factor' not in item_data:
                            item_data['rh_factor'] = 'Positive'
                        if 'blood_group' not in item_data:
                            item_data['blood_group'] = 'O'

                    # ==========================================
                    # ✅ Table အလိုက် Status များကို ခွဲခြားပြင်ဆင်ခြင်း (INSERT)
                    # ==========================================
                    if 'status' in item_data and isinstance(item_data['status'], str):
                        if item.table_name in ['blood_requests', 'global_blood_requests']:
                            item_data['status'] = item_data['status'].upper()  # ဥပမာ - PENDING
                        elif item.table_name == 'inventory':
                            item_data['status'] = item_data['status'].title()  # ဥပမာ - Available

                    if 'urgency' in item_data and isinstance(item_data['urgency'], str):
                        item_data['urgency'] = item_data['urgency'].title()
                    
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

                if isinstance(local_updated, str):
                    try:
                        local_updated = datetime.fromisoformat(local_updated.replace("Z", "+00:00"))
                    except ValueError:
                        pass
                
                if global_updated and local_updated and isinstance(local_updated, datetime) and global_updated > local_updated:
                    print(f"⚠️ Conflict: {item.table_name} - {item.record_id}")
                    conflicts.append({
                        "id": str(item.id),
                        "record_id": str(item.record_id),
                        "table_name": item.table_name,
                        "global_data": {c.name: getattr(existing_record, c.name) for c in model.__table__.columns},
                        "local_data": item.data,
                        "message": "Global data is newer than local data"
                    })
                    GlobalSyncService._create_sync_log(db, item.id, "CONFLICT_DETECTED", conflict_details={
                        "global_updated": global_updated.isoformat(),
                        "local_updated": local_updated.isoformat() if isinstance(local_updated, datetime) else str(local_updated)
                    })
                    continue

                for key, value in item.data.items():
                    if hasattr(existing_record, key) and key not in ["id", "hospital_id", "created_at", "_updated_at"]:
                        
                        # ==========================================
                        # ✅ Table အလိုက် Status များကို ခွဲခြားပြင်ဆင်ခြင်း (UPDATE)
                        # ==========================================
                        if key == 'status' and isinstance(value, str):
                            if item.table_name in ['blood_requests', 'global_blood_requests']:
                                value = value.upper()
                            elif item.table_name == 'inventory':
                                value = value.title()
                        elif key == 'urgency' and isinstance(value, str):
                            value = value.title()
                            
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