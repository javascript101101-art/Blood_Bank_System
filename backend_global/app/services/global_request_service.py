from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.global_blood_request import GlobalBloodRequest
from app.models.hospital import Hospital
from app.models.global_inventory import GlobalInventory
from app.models.inventory import Inventory
from app.schemas.global_request_schema import GlobalBloodRequestUpdate, GlobalBloodRequestResponse
from app.schemas.global_inventory_schema import DeliverBloodRequest, GlobalInventorySummary
from app.services.global_inventory_service import GlobalInventoryService


class GlobalRequestService:

    @staticmethod
    def get_all_requests(db: Session) -> List[GlobalBloodRequest]:
        return db.query(GlobalBloodRequest).order_by(
            GlobalBloodRequest.created_at.desc()
        ).all()

    @staticmethod
    def get_request(db: Session, req_id: UUID) -> Optional[GlobalBloodRequest]:
        return db.query(GlobalBloodRequest).filter(GlobalBloodRequest.id == req_id).first()

    @staticmethod
    def update_request(
        db: Session,
        req_id: UUID,
        req_data: GlobalBloodRequestUpdate
    ) -> Optional[GlobalBloodRequest]:
        request = GlobalRequestService.get_request(db, req_id)
        if not request:
            return None

        update_data = req_data.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] != request.status:
            current_status = request.status.upper() if request.status else ""
            new_status = update_data["status"].upper()

            if new_status == "FULFILLED":
                new_status = "SUPPLIER_FULFILLED"
            
            allowed_transitions = {
                "PENDING": ["ASSIGNED", "SUPPLIER_FULFILLED", "REJECTED"],
                "ASSIGNED": ["SUPPLIER_FULFILLED", "REJECTED"],
                "SUPPLIER_FULFILLED": ["IN-TRANSIT", "DELIVERED", "REJECTED"],
                "IN-TRANSIT": ["DELIVERED", "REJECTED"],
                "DELIVERED": [],
                "REJECTED": []
            }

            if current_status in allowed_transitions:
                if new_status not in allowed_transitions[current_status]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot change status from '{request.status}' to '{new_status}'"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request with status '{request.status}' cannot be modified"
                )

            # ==========================================
            # 🩸 INVENTORY AUTOMATION LOGIC
            # ==========================================
            
            # 🟢 PENDING သို့မဟုတ် ASSIGNED မှ SUPPLIER_FULFILLED သို့ ပြောင်းလဲသည့်အခါ (သွေးထုတ်ပေးမည်)
            if current_status in ["PENDING", "ASSIGNED"] and new_status == "SUPPLIER_FULFILLED":
                
                # Global Inventory ထဲမှ သွေးထုတ်ယူပြီး Unit ID များကို တောင်းခံမည်
                removed_result = GlobalInventoryService.remove_blood(
                    db=db,
                    blood_group=request.blood_group,
                    rh_factor=request.rh_factor,
                    blood_component=request.blood_component, 
                    quantity_ml=request.quantity_ml
                )
                
                # သွေးမလောက်ပါက Error တက်မည်
                if not removed_result:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Not enough stock in Global Central Inventory!"
                    )
                
                # Unit ID များကို fulfilled_unit_ids တွင် သိမ်းဆည်းရန်
                if isinstance(removed_result, list) and len(removed_result) > 0:
                    update_data["fulfilled_unit_ids"] = ",".join(removed_result)

            update_data["status"] = new_status

        if "assigned_hospital_id" in update_data and update_data["assigned_hospital_id"]:
            hospital = db.query(Hospital).filter(Hospital.id == update_data["assigned_hospital_id"]).first()
            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assigned hospital not found"
                )

        for key, value in update_data.items():
            setattr(request, key, value)

        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def assign_request(db: Session, req_id: UUID, hospital_id: UUID) -> GlobalBloodRequest:
        request = GlobalRequestService.get_request(db, req_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        if request.status.upper() != "PENDING":
            raise HTTPException(
                status_code=400,
                detail=f"Can only assign requests with 'PENDING' status. Current: {request.status}"
            )

        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")

        request.status = "ASSIGNED"
        request.assigned_hospital_id = hospital_id
        db.commit()
        db.refresh(request)
        return request

    @staticmethod
    def fulfill_request(db: Session, req_id: UUID) -> GlobalBloodRequest:
        request = GlobalRequestService.get_request(db, req_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        req_data = GlobalBloodRequestUpdate(status="SUPPLIER_FULFILLED")
        return GlobalRequestService.update_request(db, req_id, req_data)

    @staticmethod
    def deliver_request(db: Session, req_id: UUID) -> GlobalBloodRequest:
        request = GlobalRequestService.get_request(db, req_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        req_data = GlobalBloodRequestUpdate(status="IN-TRANSIT")
        return GlobalRequestService.update_request(db, req_id, req_data)

    @staticmethod
    def get_local_inventory_by_hospital(db: Session, hospital_id: UUID) -> List[dict]:
        inventories = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.quantity_ml > 0,
            Inventory.status == "Available"
        ).all()
        
        summary = {}
        for inv in inventories:
            key = f"{inv.blood_group}_{inv.rh_factor}_{getattr(inv, 'blood_component', 'Whole_Blood')}"
            if key not in summary:
                summary[key] = {
                    "blood_group": inv.blood_group,
                    "rh_factor": inv.rh_factor,
                    "blood_component": getattr(inv, 'blood_component', 'Whole_Blood'),
                    "quantity_ml": 0
                }
            summary[key]["quantity_ml"] += inv.quantity_ml
            
        return list(summary.values())

    @staticmethod
    def get_hospital_inventory_summary(db: Session) -> dict:
        hospitals = db.query(Hospital).all()
        result = {}
        for hospital in hospitals:
            inventories = db.query(Inventory).filter(
                Inventory.hospital_id == hospital.id,
                Inventory.quantity_ml > 0,
                Inventory.status == "Available"
            ).all()
            
            if inventories:
                summary = {}
                for inv in inventories:
                    key = f"{inv.blood_group}_{inv.rh_factor}_{getattr(inv, 'blood_component', 'Whole_Blood')}"
                    if key not in summary:
                        summary[key] = {
                            "blood_group": inv.blood_group,
                            "rh_factor": inv.rh_factor,
                            "blood_component": getattr(inv, 'blood_component', 'Whole_Blood'), 
                            "quantity_ml": 0
                        }
                    summary[key]["quantity_ml"] += inv.quantity_ml

                result[str(hospital.id)] = {
                    "name": hospital.name,
                    "inventory": list(summary.values())
                }
        return result

    @staticmethod
    def get_inventory_summary(db: Session) -> List[GlobalInventorySummary]:
        return GlobalInventoryService.get_summary(db)