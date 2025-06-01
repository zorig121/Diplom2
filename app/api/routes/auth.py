# app/api/v1/routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from datetime import datetime, timedelta
from bson import ObjectId
from app.core.config import config
from app.core.security import hash_password, verify_password, create_access_token, get_current_user_from_cookie
from app.db.mongodb import get_db
from app.models.auth import UserCreate, LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", status_code=201)
async def register(user: UserCreate, db=Depends(get_db)):
    existing = await db["users"].find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Имэйл аль хэдийн бүртгэлтэй байна.")

    new_user = {
        "username": user.username,
        "email": user.email,
        "fullname": user.fullname,
        "hashed_password": hash_password(user.password),
        "roles": user.roles,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    result = await db["users"].insert_one(new_user)
    return {"message": "Хэрэглэгч амжилттай бүртгэгдлээ.", "user_id": str(result.inserted_id)}

@router.post("/login")
async def login(request: LoginRequest, response: Response, db=Depends(get_db)):
    user = await db["users"].find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="Имэйл бүртгэлгүй байна.")
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Нууц үг буруу.")

    expire_delta = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token({"sub": str(user["_id"])}, expires_delta=expire_delta)

    response.set_cookie(
        key=config.COOKIE_NAME,
        value=token,
        httponly=config.COOKIE_HTTPONLY,
        secure=config.COOKIE_SECURE,
        samesite=config.COOKIE_SAMESITE,
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return {"message": "Амжилттай нэвтэрлээ."}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(config.COOKIE_NAME)
    return {"message": "Системээс гарлаа."}

@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user_from_cookie)):
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        email=current_user["email"],
        fullname=current_user.get("fullname"),
        roles=current_user.get("roles", []),
    )
