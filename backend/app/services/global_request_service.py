from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.global_blood_request import GlobalBloodRequest
from app.models.hospital import Hospital
from app.models.sync import SyncQueue  # 🆕 Import
from app.schemas.global_request_schema import GlobalBloodRequestCreate, GlobalBloodRequestUpdate
from datetime import datetime

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
        
        # 🆕 Sync Queue ထဲထည့်ပါ (Global ကို ပို့ဖို့)
        sync_data = {
            "id": str(request.id),
            "requesting_hospital_id": str(request.requesting_hospital_id),
            "blood_group": request.blood_group,
            "rh_factor": request.rh_factor,
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
        """Local Hospital က သူ့ရဲ့ Request တွေကို ကြည့်ရန်"""
        return db.query(GlobalBloodRequest).filter(
            GlobalBloodRequest.requesting_hospital_id == hospital_id
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
        
        allowed_transitions = {
            "Pending": ["Assigned", "Rejected"],
            "Assigned": ["Approved", "Rejected"],
            "Approved": ["Fulfilled", "Rejected"],
            "Fulfilled": [],
            "Rejected": []
        }
        
        if "status" in update_data and update_data["status"] != request.status:
            if request.status in allowed_transitions:
                if update_data["status"] not in allowed_transitions[request.status]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot change status from '{request.status}' to '{update_data['status']}'"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request with status '{request.status}' cannot be modified"
                )
        
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