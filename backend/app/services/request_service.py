from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.blood_request import BloodRequest
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.models.user import User
from app.schemas.request_schema import BloodRequestCreate, BloodRequestUpdate
from datetime import datetime

class RequestService:

    # ============================================
    # Status Transition Rules (Workflow)
    # ============================================
    ALLOWED_TRANSITIONS = {
        "Pending": ["Approved", "Rejected"],
        "Approved": ["Fulfilled", "Rejected"],
    }

    TERMINAL_STATUSES = ["Fulfilled", "Rejected"]

    @staticmethod
    def create_request(db: Session, req_data: BloodRequestCreate, hospital_id: UUID, user_id: UUID) -> BloodRequest:
        """သွေးလိုအပ်ချက်အသစ် ဖန်တီးရန် (Clinic Data ကို Auto ဖြည့်သွင်းခြင်း)"""
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.clinic_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinic profile not found. Cannot auto-fill clinic details."
            )
            
        profile = user.clinic_profile

        request_dict = req_data.model_dump(exclude_unset=True)
        request = BloodRequest(
            **request_dict,
            hospital_id=hospital_id,
            requested_by_user_id=user_id,
            status="Pending",
            clinic_name=profile.clinic_name,
            license=profile.license,
            contact_phone=profile.contact_phone,
            contact_email=profile.contact_email,
            clinic_address=profile.clinic_address
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)

        RequestService._add_to_sync_queue(db, request, "INSERT")
        return request

    @staticmethod
    def get_requests(db: Session, hospital_id: UUID, current_user: User = None) -> List[BloodRequest]:
        query = db.query(BloodRequest).filter(BloodRequest.hospital_id == hospital_id)
        
        if current_user and current_user.role == "Clinic":
            query = query.filter(BloodRequest.requested_by_user_id == current_user.id)
            
        return query.order_by(BloodRequest.created_at.desc()).all()

    @staticmethod
    def get_request(db: Session, req_id: UUID, hospital_id: UUID) -> Optional[BloodRequest]:
        return db.query(BloodRequest).filter(BloodRequest.id == req_id, BloodRequest.hospital_id == hospital_id).first()

    @staticmethod
    def update_request(db: Session, req_id: UUID, hospital_id: UUID, req_data: BloodRequestUpdate) -> Optional[BloodRequest]:
        """သွေးလိုအပ်ချက်ကို ပြင်ဆင်ရန်"""
        request = RequestService.get_request(db, req_id, hospital_id)
        if not request:
            return None

        old_status = request.status
        update_data = req_data.model_dump(exclude_unset=True)
        new_status = update_data.get("status")

        if new_status and new_status != old_status:

            if old_status in RequestService.TERMINAL_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request with status '{old_status}' cannot be modified."
                )

            if old_status in RequestService.ALLOWED_TRANSITIONS:
                if new_status not in RequestService.ALLOWED_TRANSITIONS[old_status]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot change status from '{old_status}' to '{new_status}'. Allowed: {RequestService.ALLOWED_TRANSITIONS[old_status]}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status '{old_status}' for transition."
                )

            # Approved → Fulfilled ဆိုရင် Inventory ကို လျှော့ပါမည်
            if new_status == "Fulfilled" and old_status == "Approved":
                RequestService._decrement_inventory(db, request)

        for key, value in update_data.items():
            setattr(request, key, value)

        if request.status == "Fulfilled" and request.fulfilled_at is None:
            request.fulfilled_at = datetime.utcnow()

        db.commit()
        db.refresh(request)

        RequestService._add_to_sync_queue(db, request, "UPDATE")
        return request

    @staticmethod
    def _decrement_inventory(db: Session, request: BloodRequest):
        """Request Fulfilled ဖြစ်ရင် Inventory ထဲက သွေးအိတ်အရေအတွက် (Units) ကိုက်ညီစွာ လျှော့ပေးပါ"""
        
        bg_parts = request.blood_group.split(" ")
        req_bg = bg_parts[0] if len(bg_parts) > 0 else request.blood_group
        req_rh = bg_parts[1] if len(bg_parts) > 1 else "Positive"

        required_units = request.quantity_units
        required_ml = getattr(request, 'volume_per_unit_ml', 500)

        # 🟢 `with_for_update()` ကို သုံး၍ အခြားသူများ ဝင်ယူခြင်းမပြုနိုင်ရန် Lock ချထားပါမည်
        available_items = db.query(Inventory).filter(
            Inventory.hospital_id == request.hospital_id,
            Inventory.blood_component == request.blood_component,
            Inventory.blood_group == req_bg,
            Inventory.rh_factor == req_rh,
            Inventory.quantity_ml >= required_ml, 
            Inventory.status == "Available"
        ).with_for_update().order_by(Inventory.expiry_date.asc()).limit(required_units).all()

        if len(available_items) < required_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"သွေးလက်ကျန် မလုံလောက်ပါ။ {required_ml}ml ပါဝင်သော အိတ် ({required_units}) အိတ် လိုအပ်သော်လည်း၊ လက်ရှိတွင် ကိုက်ညီသော ({len(available_items)}) အိတ်သာ ရှိပါသည်။"
            )

        used_unit_ids = []

        for item in available_items:
            if item.unit_id:
                used_unit_ids.append(item.unit_id)
                
            item.status = "Used"  
            item.blood_request_id = request.id  
            db.add(item)

            inv_sync_data = {
                "unit_id": item.unit_id, 
                "blood_component": item.blood_component,
                "blood_group": item.blood_group,
                "rh_factor": item.rh_factor,
                "quantity_ml": item.quantity_ml,
                "expiry_date": str(item.expiry_date),
                "status": item.status,
                "blood_request_id": str(request.id) if request.id else None 
            }
            inv_sync_entry = SyncQueue(
                hospital_id=request.hospital_id,
                table_name="inventory",
                record_id=item.id,
                operation="UPDATE",
                data=inv_sync_data,
                status="PENDING"
            )
            db.add(inv_sync_entry)
            
        if used_unit_ids:
            request.fulfilled_unit_ids = ",".join(used_unit_ids)
            
        db.commit()

    @staticmethod
    def delete_request(db: Session, req_id: UUID, hospital_id: UUID) -> bool:
        request = RequestService.get_request(db, req_id, hospital_id)
        if not request:
            return False

        if request.status in RequestService.TERMINAL_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete request with status '{request.status}'."
            )

        RequestService._add_to_sync_queue(db, request, "DELETE", delete=True)
        db.delete(request)
        db.commit()
        return True

    @staticmethod
    def _add_to_sync_queue(db: Session, request: BloodRequest, operation: str, delete: bool = False):
        """
        🛑 Privacy Protection (Data Localization)
        Local ဆေးရုံသို့ ဆေးခန်းများမှ သွေးတောင်းခံသည့် အချက်အလက် (Clinic Info, Patient Condition) များကို
        Global Central Hub သို့ Sync မလုပ်တော့ပါ။ (Local တွင်သာ သိမ်းဆည်းမည်)
        """
        pass # Sync Queue ထဲသို့ မထည့်ဘဲ ကျော်သွားပါမည်