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
# 🆕 Granular Permission Checker (Global)
# ============================================
def permission_required(resource: str, action: str):
    """
    Global Server အတွက် Permission Checker
    - Global_Admin: ဆေးရုံတွေကို Register/Update/Delete လုပ်နိုင်တယ်။
    - အခြား Roles တွေက Global Server ကို မဝင်ရဘူး (ဒါမှမဟုတ် Read-Only)
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        # Global Admin က ဆေးရုံတွေကိုပဲ စီမံခွင့်ရှိမယ်
        if current_user.role == "Global_Admin":
            if resource == "hospitals":
                return current_user
            # Global Admin က တစ်ခြား Resource တွေကို မပြင်ရဘူး
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Global Admin cannot access {resource}."
            )
        
        # တစ်ခြား Roles တွေက Global Server ကို မဝင်ရဘူး
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only Global Admin can access this server."
        )
    return permission_checker