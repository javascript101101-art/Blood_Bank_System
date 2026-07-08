from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.schemas.auth_schema import RegisterRequest
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None

    # 🆕 Self-Registration
    @staticmethod
    def register_user(db: Session, register_data: RegisterRequest, hospital_id: str) -> dict:
        # ၁။ Username ရှိပြီးသားလား စစ်ပါ
        existing_user = db.query(User).filter(User.username == register_data.username).first()
        if existing_user:
            raise ValueError("Username already exists")

        # ၂။ User အသစ်ဖန်တီးပါ (is_approved = False)
        new_user = User(
            id=uuid.uuid4(),
            hospital_id=hospital_id,
            username=register_data.username,
            hashed_password=AuthService.get_password_hash(register_data.password),
            full_name=register_data.full_name,
            role=register_data.role,
            is_active=True,
            is_approved=False  # Admin က Approve လုပ်မှသာ Login ဝင်လို့ရမယ်
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": str(new_user.id),
            "username": new_user.username,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "is_approved": new_user.is_approved,
            "message": "Registration successful. Please wait for admin approval."
        }

    # 🆕 Admin Approval for Staff
    @staticmethod
    def approve_user(db: Session, user_id: str, approved_by: User) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.is_approved:
            raise ValueError("User already approved")

        # Admin က Approve လုပ်ပါ
        user.is_approved = True
        db.commit()
        db.refresh(user)

        return {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_approved": user.is_approved,
            "message": f"User {user.username} approved successfully."
        }