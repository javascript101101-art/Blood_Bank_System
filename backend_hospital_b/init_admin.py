import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User
from app.models.hospital import Hospital
from app.services.auth_service import AuthService
import uuid

def create_admin_user():
    db = SessionLocal()
    try:
        hospital = db.query(Hospital).filter(Hospital.name == "Hospital B").first()
        if not hospital:
            print("❌ Hospital B not found. Please run SQL scripts first.")
            return

        existing_user = db.query(User).filter(User.username == "admin_b").first()
        if existing_user:
            print(f"⚠️ Admin user already exists (ID: {existing_user.id})")
            existing_user.hashed_password = AuthService.get_password_hash("admin123")
            db.commit()
            print(f"✅ Password updated for existing Admin")
            return

        admin_user = User(
            id=uuid.uuid4(),
            hospital_id=hospital.id,
            username="admin_b",
            hashed_password=AuthService.get_password_hash("admin123"),
            full_name="Hospital B Administrator",
            role="Hospital_Admin",
            is_active=True,
            is_approved=True
        )
        db.add(admin_user)
        db.commit()
        print(f"✅ Admin user created successfully!")
        print(f"   Username: admin_b")
        print(f"   Password: admin123")
        print(f"   Role: Hospital_Admin")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()