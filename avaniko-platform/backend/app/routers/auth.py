from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from database import get_db, User
from services.auth import hash_password, verify_password, create_jwt

router = APIRouter(prefix="/auth", tags=["Auth"])

class SignupRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

@router.post("/signup")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(User).where(User.email == req.email))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    user = User(
        email    = req.email,
        name     = req.name,
        password = hash_password(req.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_jwt(str(user.id), user.role)
    return {
        "user_id": str(user.id),
        "name":    user.name,
        "email":   user.email,
        "token":   token,
        "message": "Account created successfully"
    }

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user   = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account suspended")

    token = create_jwt(str(user.id), user.role)
    return {
        "user_id": str(user.id),
        "name":    user.name,
        "email":   user.email,
        "role":    user.role,
        "token":   token
    }

@router.get("/me")
async def me(db: AsyncSession = Depends(get_db),
             user: dict = Depends(__import__('services.auth', fromlist=['require_jwt']).require_jwt)):
    result = await db.execute(select(User).where(User.id == user["user_id"]))
    u      = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    return {
        "user_id":    str(u.id),
        "name":       u.name,
        "email":      u.email,
        "role":       u.role,
        "created_at": u.created_at
    }
