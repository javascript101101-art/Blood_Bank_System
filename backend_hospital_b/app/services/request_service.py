from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.blood_request import BloodRequest
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
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
        """သွေးလိုအပ်ချက်အသစ် ဖန်တီးရန်"""
        # Staff က status ကို Pending ပဲ သတ်မှတ်ပါ
        req_data.status = "Pending"
        request = BloodRequest(
            **req_data.model_dump(),
            hospital_id=hospital_id,
            requested_by_user_id=user_id
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        RequestService._add_to_sync_queue(db, request, "INSERT")
        return request

    @staticmethod
    def get_requests(db: Session, hospital_id: UUID) -> List[BloodRequest]:
        """သွေးလိုအပ်ချက်အားလုံး ကြည့်ရန်"""
        return db.query(BloodRequest).filter(BloodRequest.hospital_id == hospital_id).all()

    @staticmethod
    def get_request(db: Session, req_id: UUID, hospital_id: UUID) -> Optional[BloodRequest]:
        """သွေးလိုအပ်ချက်တစ်ခုကို ကြည့်ရန်"""
        return db.query(BloodRequest).filter(BloodRequest.id == req_id, BloodRequest.hospital_id == hospital_id).first()

    @staticmethod
    def update_request(db: Session, req_id: UUID, hospital_id: UUID, req_data: BloodRequestUpdate) -> Optional[BloodRequest]:
        """
        သွေးလိုအပ်ချက်ကို ပြင်ဆင်ရန်
        - Status Transition Rules ကို လိုက်နာရမယ်
        - Approved → Fulfilled ဖြစ်မှသာ Inventory ကို လျှော့ပေးမယ်
        """
        request = RequestService.get_request(db, req_id, hospital_id)
        if not request:
            return None

        old_status = request.status

        # ============================================
        # req_data ထဲက status ကို ယူပါ
        # ============================================
        update_data = req_data.model_dump(exclude_unset=True)
        new_status = update_data.get("status")

        # status ကို ပြောင်းချင်တယ်ဆိုရင်
        if new_status and new_status != old_status:

            # ၁။ Terminal Status (Fulfilled/Rejected) ကနေ ပြောင်းလို့မရဘူး
            if old_status in RequestService.TERMINAL_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request with status '{old_status}' cannot be modified."
                )

            # ၂။ Allowed Transitions နဲ့ ကိုက်ညီမှု ရှိမရှိ စစ်ပါ
            if old_status in RequestService.ALLOWED_TRANSITIONS:
                if new_status not in RequestService.ALLOWED_TRANSITIONS[old_status]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot change status from '{old_status}' to '{new_status}'. "
                               f"Allowed: {RequestService.ALLOWED_TRANSITIONS[old_status]}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status '{old_status}' for transition."
                )

            # ၃။ Approved → Fulfilled ဆိုရင် Inventory ကို လျှော့ပါ
            if new_status == "Fulfilled" and old_status == "Approved":
                RequestService._decrement_inventory(db, request)

        # ============================================
        # Update Request (Status အပါအဝင် အကုန်ပြင်ပါ)
        # ============================================
        for key, value in update_data.items():
            setattr(request, key, value)

        # Fulfilled ဖြစ်ရင် fulfilled_at ကို ထည့်ပါ
        if request.status == "Fulfilled" and request.fulfilled_at is None:
            request.fulfilled_at = datetime.utcnow()

        db.commit()
        db.refresh(request)

        # Sync Queue ထဲထည့်ပါ
        RequestService._add_to_sync_queue(db, request, "UPDATE")
        return request

    @staticmethod
    def _decrement_inventory(db: Session, request: BloodRequest):
        """
        Request Fulfilled ဖြစ်ရင် Inventory ထဲက သွေးပမာဏကို လျှော့ပေးပါ
        """
        inventory_item = db.query(Inventory).filter(
            Inventory.hospital_id == request.hospital_id,
            Inventory.blood_group == request.blood_group,
            Inventory.rh_factor == request.rh_factor,
            Inventory.status == "Available"
        ).order_by(Inventory.expiry_date).first()

        if not inventory_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for {request.blood_group} {request.rh_factor}"
            )

        if inventory_item.quantity_ml < request.quantity_ml:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough quantity. Available: {inventory_item.quantity_ml}ml, Required: {request.quantity_ml}ml"
            )

        inventory_item.quantity_ml -= request.quantity_ml
        if inventory_item.quantity_ml == 0:
            inventory_item.status = "Expired"

        db.add(inventory_item)

        inv_sync_data = {
            "blood_group": inventory_item.blood_group,
            "rh_factor": inventory_item.rh_factor,
            "quantity_ml": inventory_item.quantity_ml,
            "expiry_date": str(inventory_item.expiry_date),
            "status": inventory_item.status
        }
        inv_sync_entry = SyncQueue(
            hospital_id=request.hospital_id,
            table_name="inventory",
            record_id=inventory_item.id,
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
        data = {
            "patient_name": request.patient_name,
            "blood_group": request.blood_group,
            "rh_factor": request.rh_factor,
            "quantity_ml": request.quantity_ml,
            "urgency": request.urgency,
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