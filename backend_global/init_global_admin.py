import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User
from app.models.hospital import Hospital
from app.services.auth_service import AuthService
import uuid

def create_global_admin():
    db = SessionLocal()
    try:
        # Global Admin User ရှိပြီးသားလား စစ်ပါ
        existing = db.query(User).filter(User.username == "global_admin").first()
        if existing:
            print(f"⚠️ Global Admin already exists (ID: {existing.id})")
            return

        # Global Admin အသစ် (hospital_id = NULL)
        admin = User(
            id=uuid.uuid4(),
            hospital_id=None,  # Global Admin က ဆေးရုံမရှိ
            username="global_admin",
            hashed_password=AuthService.get_password_hash("admin123"),
            full_name="Global System Administrator",
            role="Global_Admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"✅ Global Admin user created successfully!")
        print(f"   Username: global_admin")
        print(f"   Password: admin123")
        print(f"   Role: Global_Admin")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_global_admin()