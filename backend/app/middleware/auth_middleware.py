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
# 🆕 Granular Permission Checker
# ============================================
def permission_required(resource: str, action: str):
    """
    Example usage:
        @permission_required("donors", "delete")
        def delete_donor(...):
            ...
    
    Permission Matrix:
        - Global_Admin: Can manage hospitals, but cannot modify local data (donors, inventory, requests)
        - Hospital_Admin: Can manage all local data for their own hospital only
        - Lab_Staff / Receptionist: Read-only (view only)
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        # Global Admin က ဆေးရုံ Data ကို မပြင်ရဘူး
        if current_user.role == "Global_Admin":
            # Global Admin က ဆေးရုံတွေကို စီမံခွင့်ရှိမယ် (ဒါပေမယ့် Local Data ကို မပြင်ရဘူး)
            if resource in ["donors", "inventory", "blood_requests"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Global Admin cannot modify {resource}. This is for local hospital admins only."
                )
            # Global Admin က ဒီ resource ကို လုပ်ခွင့်ရှိရင် return ပြန်ပါ
            return current_user
        
        # Hospital Admin က သူ့ဆေးရုံ Data ကိုပဲ ပြင်ရမယ်
        if current_user.role == "Hospital_Admin":
            # Hospital Admin က သူ့ဆေးရုံ ID ကို စစ်ဆေးပါ (ဒါက နောက်ထပ် လုံခြုံရေးအတွက်)
            # ဒါပေမယ့် ဒီအဆင့်မှာ hospital_id ကို စစ်ဆေးဖို့ လိုပါတယ် (ဒါက Services ထဲမှာ ထပ်စစ်နိုင်တယ်)
            return current_user
        
        # Lab_Staff နဲ့ Receptionist က Read-Only ဖြစ်ပါတယ်
        if current_user.role in ["Lab_Staff", "Receptionist"]:
            if action in ["create", "update", "delete"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{current_user.role} does not have permission to {action} {resource}."
                )
            return current_user
        
        # ကျန်တဲ့ Roles တွေအတွက် (အပိုထပ်ထည့်ထားတဲ့ Roles)
        return current_user
    return permission_checker