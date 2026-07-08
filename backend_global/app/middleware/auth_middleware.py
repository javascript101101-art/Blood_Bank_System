from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = AuthService.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def role_required(required_role: str):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required. You are '{current_user.role}'."
            )
        return current_user
    return role_checker

# ============================================
# 🆕 Granular Permission Checker (FIXED)
# ============================================
def permission_required(resource: str, action: str):
    """
    Permission Matrix:
    - Global_Admin: Can manage hospitals, cannot modify local data
    - Hospital_Admin: Can manage all local data (create, read, update, delete, approve)
    - Lab_Staff / Receptionist: Can create requests only (read-only for others)
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        
        # ============================================
        # 1. Global Admin
        # ============================================
        if current_user.role == "Global_Admin":
            if resource in ["donors", "inventory", "blood_requests"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Global Admin cannot modify {resource}."
                )
            return current_user

        # ============================================
        # 2. Hospital Admin - ★★★ အကုန်လုံးလုပ်ခွင့်ရှိတယ် ★★★
        # ============================================
        if current_user.role == "Hospital_Admin":
            # ★ Admin က ဘာ resource ကိုမဆို လုပ်ခွင့်ရှိတယ်
            return current_user

        # ============================================
        # 3. Staff / Receptionist - Request Create ပဲလုပ်ခွင့်ရှိတယ်
        # ============================================
        if current_user.role in ["Lab_Staff", "Receptionist"]:
            # Request Create လုပ်ခွင့်ရှိတယ်
            if resource == "blood_requests" and action == "create":
                return current_user
            
            # Approve/Reject/Fulfill/Delete/Update လုပ်ခွင့်မရှိဘူး
            if resource == "blood_requests" and action in ["approve", "update", "delete"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{current_user.role} does not have permission to {action} {resource}."
                )
            
            # တစ်ခြား Resources (donors, inventory) ကို မပြင်ရဘူး
            if resource in ["donors", "inventory"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{current_user.role} does not have permission to {action} {resource}."
                )
            
            return current_user

        # Fallback
        return current_user
    return permission_checker