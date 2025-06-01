from typing import List, Optional
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    fullname: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    fullname: Optional[str]
    password: str
    roles: List[str] = ["user"]  # 🔹 default нь user, гэхдээ ["admin"] гэж илгээж болно

class VerifyOTPRequest(BaseModel):
    otp: str
    new_password: str
