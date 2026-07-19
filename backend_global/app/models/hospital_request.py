from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import uuid
from datetime import datetime

class HospitalRequest(BaseModel):
    __tablename__ = "hospital_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    rejection_reason = Column(Text, nullable=True)
    hospital_id = Column(UUID(as_uuid=True), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<HospitalRequest {self.hospital_name} - {self.status}>"