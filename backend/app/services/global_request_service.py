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
            "blood_component": request.blood_component, 
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

        # ==========================================
        # 🟢 Global မှ တွဲပို့လိုက်သော Unit ID များကို ဖမ်းယူခြင်း
        # ==========================================
        unit_ids_str = getattr(request, 'fulfilled_unit_ids', None)
        unit_ids = [uid.strip() for uid in unit_ids_str.split(',')] if unit_ids_str else [None]
        
        # Unit ID အရေအတွက်အတိုင်း သွေးပမာဏကို ခွဲဝေမည် (ဥပမာ 1500ml ကို 3 အိတ်ဆိုလျှင် 500ml စီ)
        quantity_per_bag = request.quantity_ml // len(unit_ids) if len(unit_ids) > 0 else request.quantity_ml
        
        added_inv_ids = []

        # 🟢 သွေးအိတ်အရေအတွက် အတိုင်း Loop ပတ်၍ Local Inventory ထဲ သီးသန့်စီ သိမ်းပါမည်
        for uid in unit_ids:
            new_inventory = Inventory(
                hospital_id=hospital_id,
                unit_id=uid if uid else None, # 🟢 Unit ID အတိအကျ ထည့်သွင်းခြင်း
                blood_group=request.blood_group,
                rh_factor=request.rh_factor,
                blood_component=request.blood_component,
                quantity_ml=quantity_per_bag, 
                expiry_date=datetime.now().date() + timedelta(days=35),
                status="Available"
            )
            
            if hasattr(new_inventory, 'supplier'):
                new_inventory.supplier = "Global Hub"

            db.add(new_inventory)
            db.flush() 
            added_inv_ids.append(str(new_inventory.id))

            # 🟢 SyncQueue ထဲသို့ Unit ID နှင့်တကွ ပြန်ထည့်ပေးခြင်း
            inv_sync_data = {
                "blood_group": new_inventory.blood_group,
                "rh_factor": new_inventory.rh_factor,
                "blood_component": new_inventory.blood_component,
                "quantity_ml": new_inventory.quantity_ml,
                "expiry_date": str(new_inventory.expiry_date),
                "status": new_inventory.status
            }
            if uid:
                inv_sync_data["unit_id"] = uid
            if hasattr(new_inventory, 'supplier'):
                inv_sync_data["supplier"] = "Global Hub"

            inv_sync = SyncQueue(
                hospital_id=hospital_id,
                table_name="inventory",
                record_id=new_inventory.id,
                operation="INSERT",
                data=inv_sync_data,
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
            "message": f"Blood received! {len(unit_ids)} new inventory bag(s) added successfully.",
            "request_id": str(request.id),
            "blood_group": request.blood_group,
            "rh_factor": request.rh_factor,
            "blood_component": request.blood_component,
            "total_quantity_added": request.quantity_ml,
            "inventory_ids": added_inv_ids
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

        available_inventory = db.query(Inventory).filter(
            Inventory.hospital_id == hospital_id,
            Inventory.blood_group == request.blood_group,
            Inventory.rh_factor == request.rh_factor,
            Inventory.blood_component == request.blood_component, 
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
        
        # 🟢 [အရေးကြီး ပြင်ဆင်ချက်] သုံးလိုက်သော သွေးအိတ်များ၏ Unit ID များကို မှတ်သားရန် List ဆောက်ပါမည်
        used_unit_ids = []

        for inv in available_inventory:
            if remaining_to_deduct <= 0:
                break

            deduct_amount = min(inv.quantity_ml, remaining_to_deduct)
            inv.quantity_ml -= deduct_amount
            remaining_to_deduct -= deduct_amount
            
            # 🟢 Unit ID ပါရှိပါက မှတ်သားထားပါမည်
            if inv.unit_id and inv.unit_id not in used_unit_ids:
                used_unit_ids.append(inv.unit_id)

            if inv.quantity_ml == 0:
                inv.status = "Used"

            inv_sync = SyncQueue(
                hospital_id=hospital_id,
                table_name="inventory",
                record_id=inv.id,
                operation="UPDATE",
                data={
                    "unit_id": inv.unit_id, # 🟢 Sync Data တွင် Unit ID ပါ တွဲပို့ပေးပါမည်
                    "quantity_ml": inv.quantity_ml,
                    "status": inv.status
                },
                status="PENDING"
            )
            db.add(inv_sync)

        request.status = "Supplier_Fulfilled"
        
        # 🟢 [အရေးကြီး ပြင်ဆင်ချက်] Local Database တွင်လည်း fulfilled_unit_ids ကော်လံရှိပါက သိမ်းဆည်းပေးပါမည်
        fulfilled_unit_ids_str = ",".join(used_unit_ids) if used_unit_ids else None
        if hasattr(request, 'fulfilled_unit_ids'):
            request.fulfilled_unit_ids = fulfilled_unit_ids_str

        # 🟢 Global သို့ Request Data Sync ပို့ရာတွင် Unit ID များပါ တွဲပို့ပေးပါမည်
        sync_req_data = {
            "id": str(request.id),
            "status": request.status
        }
        if fulfilled_unit_ids_str:
            sync_req_data["fulfilled_unit_ids"] = fulfilled_unit_ids_str

        req_sync = SyncQueue(
            hospital_id=hospital_id,
            table_name="global_blood_requests",
            record_id=request.id,
            operation="UPDATE",
            data=sync_req_data, # 🟢 Unit ID ပါဝင်သော data ကို ပို့ပါမည်
            status="PENDING"
        )
        db.add(req_sync)

        db.commit()
        db.refresh(request)

        return {
            "message": "Blood fulfilled successfully! Deducted from local inventory.",
            "request_id": str(request.id),
            "deducted_ml": request.quantity_ml,
            "status": request.status,
            "unit_ids": used_unit_ids
        }