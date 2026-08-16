from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from app.models.global_blood_request import GlobalBloodRequest
from app.models.hospital import Hospital
from app.models.inventory import Inventory
from app.models.sync import SyncQueue
from app.schemas.global_request_schema import GlobalBloodRequestCreate, GlobalBloodRequestUpdate

class GlobalRequestService:

    @staticmethod
    def create_global_request(
        db: Session,
        req_data: GlobalBloodRequestCreate,
        requesting_hospital_id: UUID
    ) -> GlobalBloodRequest:
        """Local Hospital က Global ဆီ Request တင်ခြင်း"""
        request = GlobalBloodRequest(
            **req_data.model_dump(),
            requesting_hospital_id=requesting_hospital_id,
            status="Pending"
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        # Sync Queue ထဲထည့်ပါ (Global ကို ပို့ဖို့)
        sync_data = {
            "id": str(request.id),
            "requesting_hospital_id": str(request.requesting_hospital_id),
            "blood_group": request.blood_group,
            "rh_factor": request.rh_factor,
            "blood_component": request.blood_component, # 🟢 Component ထည့်ပေးလိုက်ပါသည်
            "quantity_ml": request.quantity_ml,
            "urgency": request.urgency,
            "status": request.status,
            "request_note": request.request_note
        }
        sync_entry = SyncQueue(
            hospital_id=requesting_hospital_id,
            table_name="global_blood_requests",
            record_id=request.id,
            operation="INSERT",
            data=sync_data,
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()

        return request

    @staticmethod
    def get_local_requests(db: Session, hospital_id: UUID) -> List[GlobalBloodRequest]:
        """Local Hospital က သူ့ရဲ့ Request တွေကို ကြည့်ရန် (Requester အနေနဲ့ကော Supplier အနေနဲ့ကော)"""
        return db.query(GlobalBloodRequest).filter(
            or_(
                GlobalBloodRequest.requesting_hospital_id == hospital_id,
                GlobalBloodRequest.assigned_hospital_id == hospital_id
            )
        ).order_by(GlobalBloodRequest.created_at.desc()).all()

    @staticmethod
    def get_all_requests(db: Session) -> List[GlobalBloodRequest]:
        """Global Admin က အကုန်ကြည့်ရန်"""
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
            current_status = request.status if request.status else ""
            new_status = update_data["status"]

            allowed_transitions = {
                "Pending": ["Assigned", "Supplier_Fulfilled", "Rejected"],
                "Assigned": ["Supplier_Fulfilled", "Rejected"],
                "Supplier_Fulfilled": ["In-Transit", "Delivered", "Rejected"],
                "In-Transit": ["Delivered", "Rejected"],
                "Delivered": [],
                "Rejected": []
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
    def receive_delivery(db: Session, req_id: UUID, hospital_id: UUID) -> dict:
        """
        🆕 Hospital A (Requesting Hospital) → Blood ရောက်ပြီ Confirm လုပ်ခြင်း
        (ရှိပြီးသားထဲ ပေါင်းမထည့်ဘဲ Global ကလာသော သွေးအိတ်အသစ်အဖြစ် Inventory တွင် မှတ်တမ်းတင်မည်)
        """
        request = db.query(GlobalBloodRequest).filter(
            GlobalBloodRequest.id == req_id,
            GlobalBloodRequest.requesting_hospital_id == hospital_id
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        allowed_receive_statuses = ["Supplier_Fulfilled", "In-Transit"]
        if request.status not in allowed_receive_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Can only receive requests with 'In-Transit' status. Current: {request.status}"
            )

        # 🟢 ရှိပြီးသားကို သွားမရှာတော့ဘဲ၊ Global ကပို့လိုက်သော Component ဖြင့် သွေးအိတ်အသစ် (Inventory Record) အမြဲဖန်တီးမည်
        new_inventory = Inventory(
            hospital_id=hospital_id,
            blood_group=request.blood_group,
            rh_factor=request.rh_factor,
            blood_component=request.blood_component, # 🟢 Component မှန်ကန်စွာ ဝင်မည်
            quantity_ml=request.quantity_ml,
            expiry_date=datetime.now().date() + timedelta(days=35), # ပုံမှန်အားဖြင့် ၃၅ ရက် သက်တမ်းထားသည်
            status="Available"
        )
        db.add(new_inventory)
        db.flush() 
        inv_id = str(new_inventory.id)

        inv_sync = SyncQueue(
            hospital_id=hospital_id,
            table_name="inventory",
            record_id=new_inventory.id,
            operation="INSERT",
            data={
                "blood_group": new_inventory.blood_group,
                "rh_factor": new_inventory.rh_factor,
                "blood_component": new_inventory.blood_component,
                "quantity_ml": new_inventory.quantity_ml,
                "expiry_date": str(new_inventory.expiry_date),
                "status": new_inventory.status
            },
            status="PENDING"
        )
        db.add(inv_sync)

        request.status = "Delivered"
        db.commit()
        db.refresh(request)

        req_sync = SyncQueue(
            hospital_id=hospital_id,
            table_name="global_blood_requests",
            record_id=request.id,
            operation="UPDATE",
            data={
                "id": str(request.id),
                "requesting_hospital_id": str(request.requesting_hospital_id),
                "blood_group": request.blood_group,
                "rh_factor": request.rh_factor,
                "blood_component": request.blood_component, 
                "quantity_ml": request.quantity_ml,
                "urgency": request.urgency,
                "status": request.status,
                "assigned_hospital_id": str(request.assigned_hospital_id) if request.assigned_hospital_id else None,
                "request_note": request.request_note
            },
            status="PENDING"
        )
        db.add(req_sync)
        db.commit()

        return {
            "message": "Blood received! New inventory bag added successfully.",
            "request_id": str(request.id),
            "blood_group": request.blood_group,
            "rh_factor": request.rh_factor,
            "blood_component": request.blood_component,
            "quantity_added": request.quantity_ml,
            "inventory_id": inv_id
        }

    @staticmethod
    def fulfill_request_to_global(db: Session, req_id: UUID, hospital_id: UUID) -> dict:
        """
        🆕 Hospital A (Assigned Hospital) မှ သွေးလှူဒါန်းရန် (Fulfill)
        Local Inventory မှ သွေးနှုတ်မည်။
        """
        request = db.query(GlobalBloodRequest).filter(
            GlobalBloodRequest.id == req_id,
            GlobalBloodRequest.assigned_hospital_id == hospital_id
        ).first()

        if not request:
            raise HTTPException(status_code=404, detail="Assigned request not found")

        if request.status != "Assigned":
            raise HTTPException(
                status_code=400,
                detail=f"Can only fulfill requests with 'Assigned' status. Current: {request.status}"
            )

        # 🟢 Local Inventory တွင် ရှာရာ၌ Component ပါ တူညီမှသာ နှုတ်မည်
        available_inventory = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.blood_group == request.blood_group,
            Inventory.rh_factor == request.rh_factor,
            Inventory.blood_component == request.blood_component, # 🟢 ဤနေရာတွင် စစ်ဆေးပါသည်
            Inventory.status == "Available",
            Inventory.quantity_ml > 0
        ).order_by(Inventory.expiry_date.asc()).all()

        total_available = sum(inv.quantity_ml for inv in available_inventory)
        if total_available < request.quantity_ml:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough blood in inventory. Required: {request.quantity_ml}ml, Available: {total_available}ml"
            )

        remaining_to_deduct = request.quantity_ml
        for inv in available_inventory:
            if remaining_to_deduct <= 0:
                break

            deduct_amount = min(inv.quantity_ml, remaining_to_deduct)
            inv.quantity_ml -= deduct_amount
            remaining_to_deduct -= deduct_amount

            if inv.quantity_ml == 0:
                inv.status = "Used"

            inv_sync = SyncQueue(
                hospital_id=hospital_id,
                table_name="inventory",
                record_id=inv.id,
                operation="UPDATE",
                data={
                    "quantity_ml": inv.quantity_ml,
                    "status": inv.status
                },
                status="PENDING"
            )
            db.add(inv_sync)

        request.status = "Supplier_Fulfilled"

        req_sync = SyncQueue(
            hospital_id=hospital_id,
            table_name="global_blood_requests",
            record_id=request.id,
            operation="UPDATE",
            data={
                "id": str(request.id),
                "status": request.status
            },
            status="PENDING"
        )
        db.add(req_sync)

        db.commit()
        db.refresh(request)

        return {
            "message": "Blood fulfilled successfully! Deducted from local inventory.",
            "request_id": str(request.id),
            "deducted_ml": request.quantity_ml,
            "status": request.status
        }