from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models.base import Base

# Global Models အားလုံးကို Import လုပ်ပါ
from app.models.hospital import Hospital
from app.models.user import User
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.sync import SyncQueue, SyncLog

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()