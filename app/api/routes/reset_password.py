# app/api/v1/routes/reset_password.py

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import random
import string

from app.db.mongodb import get_db
from app.core.security import hash_password
from app.utils.email import send_email
from app.models.reset_password import PasswordResetRequest, PasswordResetVerify

router = APIRouter(prefix="/reset-password", tags=["reset-password"])

@router.post("/request")
async def request_password_reset(data: PasswordResetRequest, db=Depends(get_db)):
    user = await db["users"].find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Хэрэглэгч олдсонгүй")

    otp_code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"otp": otp_code, "otp_expires_at": expires_at}}
    )

    await send_email(
        to_email=data.email,
        subject="Нууц үг сэргээх код",
        body=f"Таны OTP код: {otp_code}"
    )

    return {"message": "OTP код илгээгдлээ"}


@router.post("/verify")
async def verify_password_reset(data: PasswordResetVerify, db=Depends(get_db)):
    user = await db["users"].find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="Хэрэглэгч олдсонгүй")

    if user.get("otp") != data.otp:
        raise HTTPException(status_code=400, detail="OTP буруу")

    if datetime.utcnow() > user.get("otp_expires_at", datetime.utcnow()):
        raise HTTPException(status_code=400, detail="OTP хугацаа дууссан")

    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hash_password(data.new_password)}, "$unset": {"otp": "", "otp_expires_at": ""}}
    )

    return {"message": "Нууц үг амжилттай шинэчлэгдлээ"}
