from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth_schema import Token, RegisterRequest, RegisterResponse
from app.middleware.auth_middleware import role_required, get_current_active_user
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============================================
# 1. Login
# ============================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # 🆕 Check if user is approved
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending approval. Please wait for admin."
        )
    
    if not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================
# 2. Self-Registration (Clinic only)
# ============================================
@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    try:
        # 🟢 Clinic ပဲ Register လုပ်လို့ရမယ်
        if register_data.role != "Clinic":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only External Clinic can register."
            )
        
        # Hospital A အတွက် (ခေတ္တအနေနဲ့ Hardcode)
        hospital_id = "11111111-1111-1111-1111-111111111111"
        
        result = AuthService.register_user(db, register_data, hospital_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================
# 🆕 3. Get Pending Users (Admin Only)
# ============================================
@router.get("/pending-users", response_model=List[dict])
def get_pending_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """
    Pending ဖြစ်နေတဲ့ Clinic Users တွေကို ပြန်ပေးပါ
    """
    pending_users = db.query(User).filter(
        User.is_approved == False,
        User.is_active == True,
        # 🟢 Clinic များကိုသာ ဆွဲထုတ်ပါမည်
        User.role == "Clinic"
    ).all()
    
    return [
        {
            "id": str(user.id),
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at
        }
        for user in pending_users
    ]

# ============================================
# 🆕 4. Approve or Reject User (Admin Only)
# ============================================
@router.put("/approve-user/{user_id}")
def approve_user(
    user_id: UUID,
    approve_data: dict,  # {"is_active": true} or {"is_active": false}
    db: Session = Depends(get_db),
    current_user: User = Depends(role_required("Hospital_Admin"))
):
    """
    Clinic User ကို Approve/Reject လုပ်ပါ
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 🟢 User က Clinic ဖြစ်မှသာ လက်ခံမည်
    if user.role != "Clinic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only clinic users can be approved"
        )
    
    # User က ပြီးသား Approved ဖြစ်နေရင်
    if user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already approved"
        )
    
    is_active = approve_data.get("is_active", False)
    
    # Approve လုပ်ပါ
    user.is_approved = True
    user.is_active = is_active
    
    db.commit()
    db.refresh(user)
    
    status_text = "approved" if is_active else "rejected"
    return {
        "message": f"User {user.username} {status_text} successfully",
        "user_id": str(user.id),
        "is_active": user.is_active,
        "is_approved": user.is_approved
    }

# ============================================
# 🆕 5. Get User Profile (For Auto-filling Clinic Data)
# ============================================
@router.get("/profile", response_model=dict)
def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    လက်ရှိ Login ဝင်ထားသော User ၏ Clinic Data များကို ယူရန်
    """
    profile = current_user.clinic_profile
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic profile not found."
        )
    
    return {
        "clinic_name": profile.clinic_name,
        "license": profile.license,
        "contact_phone": profile.contact_phone,
        "contact_email": profile.contact_email,
        "clinic_address": profile.clinic_address
    }