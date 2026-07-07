# test_orm.py
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ORM Models တွေကို Import လုပ်ပါ
from app.models.base import Base
from app.models.hospital import Hospital
from app.models.user import User
from app.models.donor import Donor
from app.models.sync import SyncQueue

# Local Database နဲ့ ချိတ်ဆက်ပါ (ခင်ဗျား DB Password ထည့်ပါ)
DATABASE_URL = "postgresql://postgres:123456@localhost/blood_local_hospital_a"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_orm():
    db = SessionLocal()
    try:
        # ၁။ Hospital A ကို ဆွဲထုတ်ကြည့်ပါ (SQL Script က ကြိုသွင်းပေးထားလို့)
        hospital_a = db.query(Hospital).filter(Hospital.name == "Hospital A").first()
        print(f"✅ Found Hospital: {hospital_a.name} with ID: {hospital_a.id}")

        # ၂။ Donor အသစ် တစ်ယောက် ထည့်ကြည့်ပါ
        new_donor = Donor(
            id=uuid.uuid4(),
            hospital_id=hospital_a.id,
            name="Mg Mg Test",
            blood_group="O",
            rh_factor="Positive",
            contact_phone="09123456789"
        )
        db.add(new_donor)
        db.commit()
        print(f"✅ Inserted Donor: {new_donor.name}")

        # ၃။ Sync Queue ထဲကို ဒီ Donor အပြောင်းအလဲကို ထည့်ကြည့်ပါ (Sync Mechanism အလုပ်လုပ်လား စစ်တာ)
        sync_entry = SyncQueue(
            id=uuid.uuid4(),
            hospital_id=hospital_a.id,
            table_name="donors",
            record_id=new_donor.id,
            operation="INSERT",
            data={"name": "Mg Mg Test", "blood_group": "O"},  # JSON Snapshot
            status="PENDING"
        )
        db.add(sync_entry)
        db.commit()
        print(f"✅ Sync Queue Entry Created with Status: {sync_entry.status}")

        print("\n🎉 ORM Models and Database are working perfectly together!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_orm()