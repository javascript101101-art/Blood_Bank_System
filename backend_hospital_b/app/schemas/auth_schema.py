from pydantic import BaseModel, Field
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
    role: str = Field("Lab_Staff", pattern="^(Lab_Staff|Receptionist)$")  # Staff ပဲ Register လုပ်လို့ရမယ်

# 🆕 Register Response Schema
class RegisterResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    is_approved: bool
    message: str