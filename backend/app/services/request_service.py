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
    
    @staticmethod
    def create_request(db: Session, req_data: BloodRequestCreate, hospital_id: UUID, user_id: UUID) -> BloodRequest:
        """သွေးလိုအပ်ချက်အသစ် ဖန်တီးရန်"""
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
        """သွေးလိုအပ်ချက်ကို ပြင်ဆင်ရန် (Fulfilled ဖြစ်ရင် Inventory ကိုလျှော့ပေးမယ်)"""
        request = RequestService.get_request(db, req_id, hospital_id)
        if not request:
            return None

        # ★★★ PHASE 2.4: Auto-Decrement Logic ★★★
        old_status = request.status
        new_status = req_data.status if hasattr(req_data, 'status') else request.status

        # Status က Fulfilled ဖြစ်သွားရင် Inventory ကို လျှော့ပါ
        if new_status == "Fulfilled" and old_status != "Fulfilled":
            # ၁။ သက်ဆိုင်ရာ Inventory ကို ရှာပါ (Available ဖြစ်ပြီး လိုအပ်တဲ့ သွေးအုပ်စုနဲ့ ကိုက်ညီတဲ့ဟာ)
            inventory_item = db.query(Inventory).filter(
                Inventory.hospital_id == hospital_id,
                Inventory.blood_group == request.blood_group,
                Inventory.rh_factor == request.rh_factor,
                Inventory.status == "Available"
            ).order_by(Inventory.expiry_date).first()  # သက်တမ်းနီးလာတဲ့ဟာကို အရင်သုံးပါ

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

            # ၂။ Inventory ကို Update လုပ်ပါ (လျှော့ပါ)
            inventory_item.quantity_ml -= request.quantity_ml
            if inventory_item.quantity_ml == 0:
                inventory_item.status = "Expired"

            db.add(inventory_item)
            
            # ၃။ Inventory Update အတွက် Sync Queue ထဲထည့်ပါ
            inv_sync_data = {
                "blood_group": inventory_item.blood_group,
                "rh_factor": inventory_item.rh_factor,
                "quantity_ml": inventory_item.quantity_ml,
                "expiry_date": str(inventory_item.expiry_date),
                "status": inventory_item.status
            }
            inv_sync_entry = SyncQueue(
                hospital_id=hospital_id,
                table_name="inventory",
                record_id=inventory_item.id,
                operation="UPDATE",
                data=inv_sync_data,
                status="PENDING"
            )
            db.add(inv_sync_entry)

        # ၄။ Request ကို Update လုပ်ပါ
        for key, value in req_data.model_dump(exclude_unset=True).items():
            setattr(request, key, value)
            
        if request.status == "Fulfilled" and request.fulfilled_at is None:
            request.fulfilled_at = datetime.utcnow()

        db.commit()
        db.refresh(request)

        # ၅။ Request အတွက် Sync Queue ထဲထည့်ပါ
        RequestService._add_to_sync_queue(db, request, "UPDATE")
        
        return request

    @staticmethod
    def delete_request(db: Session, req_id: UUID, hospital_id: UUID) -> bool:
        """သွေးလိုအပ်ချက်ကို ဖျက်ရန်"""
        request = RequestService.get_request(db, req_id, hospital_id)
        if not request:
            return False
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