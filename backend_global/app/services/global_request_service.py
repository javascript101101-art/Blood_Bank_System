from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.global_blood_request import GlobalBloodRequest
from app.models.hospital import Hospital
from app.schemas.global_request_schema import GlobalBloodRequestUpdate, GlobalBloodRequestResponse

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