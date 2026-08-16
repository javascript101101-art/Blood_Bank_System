from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, date
from typing import List, Dict, Any
import httpx
from app.models.sync import SyncQueue, SyncLog
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.global_blood_request import GlobalBloodRequest
from app.config import settings

class SyncService:
    GLOBAL_SYNC_URL = "http://localhost:8001/api/v1/sync/push"
    GLOBAL_PULL_URL = "http://localhost:8001/api/v1/global-requests/"
    GLOBAL_LOGIN_URL = "http://localhost:8001/api/v1/auth/login"
    GLOBAL_USERNAME = "global_admin"
    GLOBAL_PASSWORD = "admin123"

    @staticmethod
    def _get_global_token() -> str:
        """Fetch Access Token from the Global Server"""
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
        """Fetch PENDING Sync Queue Items"""
        return db.query(SyncQueue).filter(
            SyncQueue.hospital_id == hospital_id,
            SyncQueue.status == "PENDING"
        ).order_by(SyncQueue.created_at).all()

    @staticmethod
    def push_to_global(db: Session, hospital_id: UUID) -> Dict[str, Any]:
        """Push Local Data to Global Server"""
        print(f"--- Debug: Push API Called for Hospital ID: {hospital_id} ---")
        pending_items = SyncService.get_pending_items(db, hospital_id)
        print(f"--- Debug: Found Pending Items Count: {len(pending_items)} ---")

        if not pending_items:
            print("--- Debug: Returning 'No pending items' ---")
            return {"message": "No pending items to sync", "synced": 0, "failed": 0}

        payload = {
            "hospital_id": str(hospital_id),
            "items": [
                {
                    "id": str(item.id),
                    "table_name": item.table_name,
                    "record_id": str(item.record_id),
                    "operation": item.operation,
                    "data": {
                        k: (
                            v.upper() if k == "status" and isinstance(v, str) else 
                            v.isoformat() if hasattr(v, 'isoformat') else 
                            str(v) if isinstance(v, (datetime, date)) else 
                            v
                        )
                        for k, v in (item.data or {}).items()
                    },
                    "status": item.status,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                for item in pending_items
            ]
        }

        token = SyncService._get_global_token()
        if not token:
            return {"message": "Failed to authenticate with Global Server", "synced": 0, "failed": len(pending_items)}

        try:
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

            synced_ids = result.get("success", [])
            failed_ids = result.get("failed", [])
            conflicts = result.get("conflicts", [])

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
                    SyncService._resolve_conflict(db, item, conflict_detail)

            db.commit()
            return {
                "message": "Sync completed",
                "synced": len(synced_ids),
                "failed": len(failed_ids),
                "conflicts": len(conflicts)
            }

        except httpx.RequestError as e:
            print(f"--- Debug: Network Error connecting to Global: {str(e)} ---")
            return {"message": f"Network error: {str(e)}", "synced": 0, "failed": len(pending_items)}
        except Exception as e:
            print(f"--- Debug: General Sync Error: {str(e)} ---")
            if hasattr(e, 'response') and e.response is not None:
                print(f"--- Debug: Global Server Response Detail: {e.response.text} ---")
                
            db.rollback()
            return {"message": f"Sync error: {str(e)}", "synced": 0, "failed": len(pending_items)}

    @staticmethod
    def pull_from_global(db: Session, hospital_id: UUID) -> Dict[str, Any]:
        """Pull updated data (Status changes) from Global Server"""
        print(f"--- Debug: Pull API Called for Hospital ID: {hospital_id} ---")
        
        token = SyncService._get_global_token()
        if not token:
            return {"message": "Failed to authenticate with Global Server", "pulled": 0}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    SyncService.GLOBAL_PULL_URL,
                    headers={
                        "Authorization": f"Bearer {token}"
                    }
                )
                response.raise_for_status()
                global_requests = response.json()

            updated_count = 0
            
            status_mapping = {
                "PENDING": "Pending",
                "ASSIGNED": "Assigned",
                "SUPPLIER_FULFILLED": "Supplier_Fulfilled",
                "FULFILLED": "Supplier_Fulfilled",
                "DELIVERED": "Delivered",
                "REJECTED": "Rejected",
                "IN-TRANSIT": "In-Transit"
            }

            for g_req in global_requests:
                req_id = UUID(g_req['id'])
                req_hospital_id = UUID(g_req['requesting_hospital_id'])
                
                assigned_hosp_id = None
                if g_req.get('assigned_hospital_id'):
                    assigned_hosp_id = UUID(g_req['assigned_hospital_id'])

                local_req = db.query(GlobalBloodRequest).filter(GlobalBloodRequest.id == req_id).first()
                
                raw_g_status = g_req.get('status', 'Pending')
                mapped_status = status_mapping.get(raw_g_status.upper(), raw_g_status)

                if local_req:
                    if local_req.status != mapped_status or local_req.assigned_hospital_id != assigned_hosp_id:
                        local_req.status = mapped_status
                        local_req.assigned_hospital_id = assigned_hosp_id
                        updated_count += 1
                else:
                    new_req = GlobalBloodRequest(
                        id=req_id,
                        requesting_hospital_id=req_hospital_id,
                        blood_group=g_req['blood_group'],
                        rh_factor=g_req['rh_factor'],
                        blood_component=g_req.get('blood_component', 'Whole_Blood'), 
                        quantity_ml=g_req['quantity_ml'],
                        urgency=g_req['urgency'],
                        status=mapped_status,
                        assigned_hospital_id=assigned_hosp_id,
                        request_note=g_req.get('request_note')
                    )
                    db.add(new_req)
                    updated_count += 1

            db.commit()
            print(f"--- Debug: Pull successful. Updated {updated_count} records. ---")
            return {"message": "Pull completed successfully", "pulled": updated_count}

        except Exception as e:
            db.rollback()
            print(f"--- Debug: Pull Error: {str(e)} ---")
            return {"message": f"Pull error: {str(e)}", "pulled": 0}

    @staticmethod
    def _resolve_conflict(db: Session, item: SyncQueue, conflict_detail: dict):
        """Last-Write-Wins: Overwrite local data with global data (with Case Handling)"""
        table_name = item.table_name
        record_id = item.record_id
        global_data = conflict_detail.get("global_data", {})

        status_mapping = {
            "PENDING": "Pending",
            "ASSIGNED": "Assigned",
            "SUPPLIER_FULFILLED": "Supplier_Fulfilled",
            "FULFILLED": "Supplier_Fulfilled",
            "DELIVERED": "Delivered",
            "REJECTED": "Rejected",
            "IN-TRANSIT": "In-Transit"
        }

        if table_name == "donors":
            donor = db.query(Donor).filter(Donor.id == record_id).first()
            if donor:
                for key, value in global_data.items():
                    if hasattr(donor, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        if key == "status" and isinstance(value, str):
                            value = value.title()
                        setattr(donor, key, value)
                db.commit()
        elif table_name == "inventory":
            inventory = db.query(Inventory).filter(Inventory.id == record_id).first()
            if inventory:
                for key, value in global_data.items():
                    if hasattr(inventory, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        if key == "status" and isinstance(value, str):
                            value = value.title()
                        setattr(inventory, key, value)
                db.commit()
        elif table_name == "blood_requests":
            request = db.query(BloodRequest).filter(BloodRequest.id == record_id).first()
            if request:
                for key, value in global_data.items():
                    if hasattr(request, key) and key not in ["id", "hospital_id", "created_at", "updated_at"]:
                        if key == "status" and isinstance(value, str):
                            value = value.title()
                        setattr(request, key, value)
                db.commit()
        elif table_name == "global_blood_requests":
            global_req = db.query(GlobalBloodRequest).filter(GlobalBloodRequest.id == record_id).first()
            if global_req:
                for key, value in global_data.items():
                    if hasattr(global_req, key) and key not in ["id", "requesting_hospital_id", "created_at", "updated_at"]:
                        # 🟢 Status ကို Local Database သိသော Format ပြောင်းခြင်း
                        if key == "status" and isinstance(value, str):
                            value = status_mapping.get(value.upper(), value.title())
                        setattr(global_req, key, value)
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
        """Return the current sync status"""
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

    @staticmethod
    def receive_from_local(db: Session, payload: dict) -> dict:
        """Receive and process synced data"""
        items = payload.get("items", [])
        
        synced_ids = []
        failed_ids = []
        conflicts = []

        status_mapping = {
            "PENDING": "Pending",
            "ASSIGNED": "Assigned",
            "SUPPLIER_FULFILLED": "Supplier_Fulfilled",
            "FULFILLED": "Supplier_Fulfilled",
            "DELIVERED": "Delivered",
            "REJECTED": "Rejected",
            "IN-TRANSIT": "In-Transit"
        }

        for item in items:
            table_name = item.get("table_name")
            record_id = item.get("record_id")
            operation = item.get("operation")
            data = item.get("data")
            item_id = item.get("id")

            # 🟢 ဝင်လာသော Data ထဲမှ Status ကို စစ်ဆေး၍ Format အမှန်ချိန်းပေးခြင်း
            if data and "status" in data and isinstance(data["status"], str):
                if table_name == "global_blood_requests":
                    data["status"] = status_mapping.get(data["status"].upper(), data["status"].title())
                else:
                    data["status"] = data["status"].title()

            try:
                if table_name == "global_blood_requests":
                    existing = db.query(GlobalBloodRequest).filter(GlobalBloodRequest.id == record_id).first()
                    if operation == "INSERT" and not existing:
                        new_req = GlobalBloodRequest(**data)
                        new_req.id = record_id  
                        db.add(new_req)
                    elif operation == "UPDATE" and existing:
                        for k, v in data.items():
                            if hasattr(existing, k) and k not in ["id", "created_at", "updated_at"]:
                                setattr(existing, k, v)
                    elif operation == "DELETE" and existing:
                        db.delete(existing)

                elif table_name == "inventory":
                    existing = db.query(Inventory).filter(Inventory.id == record_id).first()
                    if operation == "INSERT" and not existing:
                        new_inv = Inventory(**data)
                        new_inv.id = record_id
                        new_inv.hospital_id = data.get("hospital_id", payload.get("hospital_id"))
                        db.add(new_inv)
                    elif operation == "UPDATE" and existing:
                        for k, v in data.items():
                            if hasattr(existing, k) and k not in ["id", "created_at", "updated_at"]:
                                setattr(existing, k, v)
                    elif operation == "DELETE" and existing:
                        db.delete(existing)

                elif table_name == "donors":
                    existing = db.query(Donor).filter(Donor.id == record_id).first()
                    if operation == "INSERT" and not existing:
                        new_donor = Donor(**data)
                        new_donor.id = record_id
                        new_donor.hospital_id = data.get("hospital_id", payload.get("hospital_id"))
                        db.add(new_donor)
                    elif operation == "UPDATE" and existing:
                        for k, v in data.items():
                            if hasattr(existing, k) and k not in ["id", "created_at", "updated_at"]:
                                setattr(existing, k, v)
                    elif operation == "DELETE" and existing:
                        db.delete(existing)

                elif table_name == "blood_requests":
                    existing = db.query(BloodRequest).filter(BloodRequest.id == record_id).first()
                    if operation == "INSERT" and not existing:
                        new_req = BloodRequest(**data)
                        new_req.id = record_id
                        new_req.hospital_id = data.get("hospital_id", payload.get("hospital_id"))
                        db.add(new_req)
                    elif operation == "UPDATE" and existing:
                        for k, v in data.items():
                            if hasattr(existing, k) and k not in ["id", "created_at", "updated_at"]:
                                setattr(existing, k, v)
                    elif operation == "DELETE" and existing:
                        db.delete(existing)

                db.commit()
                synced_ids.append(item_id)
            except Exception as e:
                db.rollback()
                failed_ids.append(item_id)
                print(f"Error syncing item {item_id}: {e}")

        return {
            "success": synced_ids,
            "failed": failed_ids,
            "conflicts": conflicts
        }