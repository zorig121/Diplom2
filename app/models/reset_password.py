from pydantic import BaseModel, EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    email: EmailStr
    otp: str
    new_password: str