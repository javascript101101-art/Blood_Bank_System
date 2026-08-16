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
        
        # 🟢 ၁။ Request တင်သည့် User နှင့် သူ၏ Clinic Profile ကို ရှာခြင်း
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.clinic_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Clinic profile not found. Cannot auto-fill clinic details."
            )
            
        profile = user.clinic_profile

        # 🟢 ၂။ Blood Request Object တည်ဆောက်ရာတွင် Profile မှ Data များ ပေါင်းထည့်ခြင်း
        request_dict = req_data.model_dump(exclude_unset=True)
        # Frontend မှ မပို့သော Data များကို Profile မှ ယူ၍ ဖြည့်စွက်ပါမည်
        request = BloodRequest(
            **request_dict,
            hospital_id=hospital_id,
            requested_by_user_id=user_id,
            status="Pending",
            # Clinic Data များကို ဤနေရာတွင် Auto ဖြည့်သွင်းပါသည်
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
        """သွေးလိုအပ်ချက်များ ကြည့်ရန် (Admin ဖြစ်လျှင် အားလုံး၊ Clinic ဖြစ်လျှင် ကိုယ်တောင်းထားသည်များကိုသာ ပြမည်)"""
        
        query = db.query(BloodRequest).filter(BloodRequest.hospital_id == hospital_id)
        
        # 🟢 ဝင်ရောက်လာသူသည် Clinic ဖြစ်ပါက ၎င်းတို့၏ User ID ဖြင့် တောင်းထားသည်များကိုသာ Filter လုပ်မည်
        if current_user and current_user.role == "Clinic":
            query = query.filter(BloodRequest.requested_by_user_id == current_user.id)
            
        return query.all()

    @staticmethod
    def get_request(db: Session, req_id: UUID, hospital_id: UUID) -> Optional[BloodRequest]:
        """သွေးလိုအပ်ချက်တစ်ခုကို ကြည့်ရန်"""
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

            # Approved → Fulfilled ဆိုရင် Inventory ကို လျှော့ပါ
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
        
        # 🟢 ၁။ သွေးအုပ်စုနှင့် RH Factor ခွဲထုတ်ခြင်း
        bg_parts = request.blood_group.split(" ")
        req_bg = bg_parts[0] if len(bg_parts) > 0 else request.blood_group
        req_rh = bg_parts[1] if len(bg_parts) > 1 else "Positive"

        # 🟢 ၂။ တောင်းဆိုထားသော အရေအတွက် (Units)
        required_units = request.quantity_units

        # 🟢 ၃။ Inventory ထဲမှ Available ဖြစ်နေသော သက်ဆိုင်ရာ သွေးအိတ်များကို အဟောင်းဆုံးမှစ၍ လိုအပ်သလောက် (limit) ဆွဲထုတ်ခြင်း
        available_items = db.query(Inventory).filter(
            Inventory.hospital_id == request.hospital_id,
            Inventory.blood_component == request.blood_component,
            Inventory.blood_group == req_bg,
            Inventory.rh_factor == req_rh,
            Inventory.status == "Available"
        ).order_by(Inventory.expiry_date.asc()).limit(required_units).all()

        # 🟢 ၄။ လုံလောက်မှု ရှိ/မရှိ စစ်ဆေးခြင်း
        if len(available_items) < required_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {request.blood_component} ({request.blood_group}). Available: {len(available_items)} units, Required: {required_units} units."
            )

        # 🟢 ၅။ လုံလောက်ပါက ဆွဲထုတ်လာသော သွေးအိတ်များအားလုံးကို "Used" ဟု ပြောင်းလဲခြင်း
        for item in available_items:
            item.status = "Used"  
            item.blood_request_id = request.id  # 🟢 အသစ် - ဘယ် Request အတွက် သုံးလိုက်လဲ မှတ်သားခြင်း
            db.add(item)

            # သွေးအိတ်တစ်ခုစီအတွက် Sync Queue ထဲသို့ သီးခြားစီ မှတ်တမ်းတင်ခြင်း
            inv_sync_data = {
                "blood_component": item.blood_component,
                "blood_group": item.blood_group,
                "rh_factor": item.rh_factor,
                "quantity_ml": item.quantity_ml,
                "expiry_date": str(item.expiry_date),
                "status": item.status,
                "blood_request_id": str(request.id) if request.id else None # 🟢 အသစ် - Global ကိုပါ Sync လှမ်းပို့ပေးမည်
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

    @staticmethod
    def delete_request(db: Session, req_id: UUID, hospital_id: UUID) -> bool:
        """သွေးလိုအပ်ချက်ကို ဖျက်ရန်"""
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
        """Sync Queue ထဲထည့်ရန်"""
        
        # 🟢 External Clinic Form နှင့် ကိုက်ညီအောင် Data Dictionary ကို အသစ် ပြင်ဆင်ထားပါသည်
        data = {
            "clinic_name": request.clinic_name,
            "license": request.license,
            "contact_phone": request.contact_phone,
            "contact_email": request.contact_email,
            "clinic_address": request.clinic_address,
            "blood_component": request.blood_component, 
            "blood_group": request.blood_group,
            "quantity_units": request.quantity_units,
            "urgency": request.urgency,
            "required_date": str(request.required_date) if request.required_date else None,
            "patient_condition": request.patient_condition,
            "status": request.status,
            "requested_by_user_id": str(request.requested_by_user_id)
        }
        if request.fulfilled_at:
            data["fulfilled_at"] = request.fulfilled_at.isoformat()

        sync_entry = SyncQueue(
            hospital_id=request.hospital_id,
            table_name="blood_requests",
            record_id=request.id,
            operation=operation,
            data=data,
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()