from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any
from app.models.donor import Donor
from app.models.inventory import Inventory
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
                    "global_blood_requests": GlobalBloodRequest
                }
                model = model_map.get(item.table_name)
                if not model:
                    print(f"❌ Unknown table or ignored table: {item.table_name}")
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

                    if 'status' in item_data and isinstance(item_data['status'], str):
                        if model == GlobalBloodRequest:
                            item_data['status'] = item_data['status'].upper()
                        else:
                            item_data['status'] = item_data['status'].title()

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
                
                gu_naive = global_updated.replace(tzinfo=None) if isinstance(global_updated, datetime) else global_updated
                lu_naive = local_updated.replace(tzinfo=None) if isinstance(local_updated, datetime) else local_updated

                incoming_status = str(item.data.get('status', '')).upper()
                terminal_statuses = ['USED', 'PROCESSED', 'EXPIRED', 'DISCARDED', 'SUPPLIER_FULFILLED', 'DELIVERED', 'REJECTED']

                if gu_naive and lu_naive and isinstance(lu_naive, datetime) and gu_naive > lu_naive:
                    if incoming_status not in terminal_statuses:
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
                            "global_updated": gu_naive.isoformat(),
                            "local_updated": lu_naive.isoformat()
                        })
                        continue
                    else:
                        print(f"⚠️ Override Conflict for Terminal Status: {incoming_status}")

                for key, value in item.data.items():
                    if hasattr(existing_record, key) and key not in ["id", "hospital_id", "created_at", "_updated_at"]:
                        if key == 'status' and isinstance(value, str):
                            if model == GlobalBloodRequest:
                                value = value.upper()
                            else:
                                value = value.title()
                        elif key == 'urgency' and isinstance(value, str):
                            value = value.title()
                            
                        setattr(existing_record, key, value)
                
                # 🟢 [အရေးကြီး ပြင်ဆင်ချက်] Inventory Table အတွက် unit_id နှင့် blood_request_id ပါလာပါက ေနာက်ဆုံးအနေဖြင့် သေချာ ချိတ်ဆက်ပေးပါမည်
                if model == Inventory:
                    if 'unit_id' in item.data:
                        setattr(existing_record, 'unit_id', item.data['unit_id'])
                    if 'blood_request_id' in item.data:
                        req_id_val = item.data['blood_request_id']
                        setattr(existing_record, 'blood_request_id', UUID(req_id_val) if req_id_val else None)

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