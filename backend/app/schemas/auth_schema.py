from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str
    role: str

# 🆕 Register Request Schema
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=100)
    # 🟢 Lab_Staff အစား Clinic ဟု ပြောင်းထားပါသည်
    role: str = Field("Clinic", pattern="^(Clinic)$")  # Clinic အနေဖြင့်သာ Register လုပ်ခွင့်ရှိမည်
    
    # 🏥 Clinic Information (Register လုပ်ချိန် Clinic Data များ ထည့်သွင်းရန်)
    clinic_name: Optional[str] = None
    license: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    clinic_address: Optional[str] = None

# 🆕 Register Response Schema
class RegisterResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    is_approved: bool
    message: str