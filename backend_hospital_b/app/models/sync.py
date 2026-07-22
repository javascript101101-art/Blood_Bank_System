from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.models.base import BaseModel

class SyncQueue(BaseModel):
    __tablename__ = "sync_queue"

    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False)
    table_name = Column(String(50), nullable=False)  # e.g., 'donors', 'inventory'
    record_id = Column(UUID(as_uuid=True), nullable=False)  # ID of the changed record
    operation = Column(String(10), nullable=False)  # INSERT, UPDATE, DELETE
    data = Column(JSONB, nullable=False)  # Full snapshot of the record
    status = Column(String(20), default="PENDING")  # PENDING, SYNCED, FAILED, CONFLICT
    retry_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime)

    # Relationship to logs
    logs = relationship("SyncLog", back_populates="sync_queue")

class SyncLog(BaseModel):
    __tablename__ = "sync_logs"

    sync_queue_id = Column(UUID(as_uuid=True), ForeignKey("sync_queue.id", ondelete="SET NULL"))
    status = Column(String(20), nullable=False)  # SUCCESS, FAILED, CONFLICT_DETECTED
    error_message = Column(Text)
    conflict_details = Column(JSONB)  # Store conflicting old/new data here
    sync_timestamp = Column(DateTime, server_default=func.now())

    sync_queue = relationship("SyncQueue", back_populates="logs")