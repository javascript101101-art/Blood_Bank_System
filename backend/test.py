"""
Step 2 Test Script - Database Connection Test
ဒီ Script က SQLAlchemy Models တွေကို PostgreSQL နဲ့ ချိတ်ဆက်ပြီး 
အလုပ်လုပ်မလုပ် စမ်းသပ်ပေးပါတယ်။
"""

import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ==========================================
# Python Path ကို သတ်မှတ်ပါ (app folder ကို ရှာတွေ့ဖို့)
# ==========================================
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# ==========================================
# ORM Models တွေကို Import လုပ်ပါ
# ==========================================
from app.models.base import Base
from app.models.hospital import Hospital
from app.models.user import User
from app.models.donor import Donor
from app.models.inventory import Inventory
from app.models.blood_request import BloodRequest
from app.models.sync import SyncQueue, SyncLog

# ==========================================
# Database Connection Settings
# ==========================================
# ခင်ဗျားရဲ့ PostgreSQL Password ကို ဒီမှာ ထည့်ပါ
POSTGRES_PASSWORD = "123456"  # <--- ခင်ဗျားရဲ့ Password နဲ့ အစားထိုးပါ
DATABASE_NAME = "blood_local_hospital_a"
DATABASE_URL = f"postgresql://postgres:{POSTGRES_PASSWORD}@localhost/{DATABASE_NAME}"

print(f"🔗 Connecting to: {DATABASE_URL}")

# SQLAlchemy Engine ကို ဖန်တီးပါ
engine = create_engine(
    DATABASE_URL,
    echo=True,  # True ဆိုရင် SQL Query တွေ အကုန်ပြမယ် (Debug အတွက်)
    pool_pre_ping=True,  # Connection ပြတ်သွားရင် ပြန်စစ်ပေးမယ်
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ==========================================
# Test Function
# ==========================================
def test_database_connection():
    """Database နဲ့ ချိတ်ဆက်ပြီး Models တွေ အလုပ်လုပ်မလုပ် စမ်းသပ်ပါ"""
    
    print("\n" + "="*50)
    print("📊 Testing Database Connection & ORM Models")
    print("="*50)
    
    # ၁။ Database Connection ကို စမ်းသပ်ပါ
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database Connection: SUCCESS")
    except Exception as e:
        print(f"❌ Database Connection: FAILED - {e}")
        return
    
    db = SessionLocal()
    try:
        # ၂။ Hospital A ကို ဆွဲထုတ်ကြည့်ပါ (SQL Script က ကြိုထည့်ပေးထားတယ်)
        hospital_a = db.query(Hospital).filter(Hospital.name == "Hospital A").first()
        
        if not hospital_a:
            print("❌ Hospital A ကို မတွေ့ပါ။")
            print("   ကျေးဇူးပြု၍ init_local_db.sql ကို ဦးစွာ Run ပါ။")
            print("   Command: psql -U postgres -d blood_local_hospital_a -f backend/scripts/init_local_db.sql")
            return
        
        print(f"✅ Hospital Found: {hospital_a.name}")
        print(f"   ID: {hospital_a.id}")
        print(f"   Location: {hospital_a.location}")
        print(f"   Contact: {hospital_a.contact_email}")

        # ၃။ Donor အသစ် တစ်ယောက် ထည့်ကြည့်ပါ
        new_donor = Donor(
            id=uuid.uuid4(),
            hospital_id=hospital_a.id,
            name="Mg Mg Test Donor",
            dob="1990-01-15",
            blood_group="O",
            rh_factor="Positive",
            contact_phone="09123456789",
            email="mgmg@example.com"
        )
        db.add(new_donor)
        db.commit()
        db.refresh(new_donor)  # created_at, updated_at ကို ပြန်ဆွဲယူမယ်
        print(f"\n✅ Donor Inserted:")
        print(f"   Name: {new_donor.name}")
        print(f"   ID: {new_donor.id}")
        print(f"   Blood Group: {new_donor.blood_group} {new_donor.rh_factor}")
        print(f"   Created At: {new_donor.created_at}")

        # ၄။ Sync Queue ထဲကို ဒီ Donor အပြောင်းအလဲကို ထည့်ကြည့်ပါ
        sync_entry = SyncQueue(
            id=uuid.uuid4(),
            hospital_id=hospital_a.id,
            table_name="donors",
            record_id=new_donor.id,
            operation="INSERT",
            data={
                "name": new_donor.name,
                "blood_group": new_donor.blood_group,
                "rh_factor": new_donor.rh_factor,
                "contact_phone": new_donor.contact_phone
            },
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()
        db.refresh(sync_entry)
        print(f"\n✅ Sync Queue Entry Created:")
        print(f"   ID: {sync_entry.id}")
        print(f"   Table: {sync_entry.table_name}")
        print(f"   Operation: {sync_entry.operation}")
        print(f"   Status: {sync_entry.status}")
        print(f"   Created At: {sync_entry.created_at}")

        # ၅။ Sync Log ထဲကို အောင်မြင်ကြောင်း မှတ်တမ်းထည့်ပါ
        sync_log = SyncLog(
            id=uuid.uuid4(),
            sync_queue_id=sync_entry.id,
            status="SUCCESS",
            error_message=None,
            conflict_details=None
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)
        print(f"\n✅ Sync Log Created:")
        print(f"   ID: {sync_log.id}")
        print(f"   Status: {sync_log.status}")
        print(f"   Timestamp: {sync_log.sync_timestamp}")

        # ၆။ ရလဒ်အားလုံးကို ပြန်ဆွဲထုတ်ကြည့်ပါ (Verification)
        print("\n" + "="*50)
        print("📋 Verification - Current Data in Database")
        print("="*50)
        
        # Donor အားလုံးကို ရေတွက်ပါ
        donor_count = db.query(Donor).filter(Donor.hospital_id == hospital_a.id).count()
        print(f"Total Donors in Hospital A: {donor_count}")
        
        # Sync Queue အားလုံးကို ရေတွက်ပါ
        pending_count = db.query(SyncQueue).filter(SyncQueue.status == "PENDING").count()
        synced_count = db.query(SyncQueue).filter(SyncQueue.status == "SYNCED").count()
        print(f"Sync Queue - PENDING: {pending_count}, SYNCED: {synced_count}")
        
        # Sync Log အားလုံးကို ရေတွက်ပါ
        log_count = db.query(SyncLog).count()
        print(f"Sync Logs Total: {log_count}")

        print("\n" + "="*50)
        print("🎉 အောင်မြင်ပါပြီ! Step 2 ရဲ့ ORM Models နဲ့ Database တွေ အလုပ်လုပ်နေပါပြီ။")
        print("="*50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        print("\n🔍 Error Details:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n🔒 Database connection closed.")

# ==========================================
# Run Test
# ==========================================
if __name__ == "__main__":
    test_database_connection()