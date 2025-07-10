from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from src.models.firebase import firebase_db
from settings import settings
from src.dependencies.auth import get_current_user, TokenData

auth_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    email: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    data.update({"exp": expire})
    return jwt.encode(data, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

async def get_user(username: str):
    docs = firebase_db.collection("users").where("username", "==", username).stream()
    async for doc in docs:
        return doc.to_dict()
    return None

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

@auth_router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate):
    if await get_user(user.username):
        raise HTTPException(400, "Username already exists")

    email_check = firebase_db.collection("users").where("email", "==", user.email).stream()
    async for _ in email_check:
        raise HTTPException(400, "Email already registered")

    hashed_password = get_password_hash(user.password)
    data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    firebase_db.collection("users").add(data)
    return UserResponse(**{k: data[k] for k in ("username", "email", "created_at")})

@auth_router.post("/token", response_model=Token)
async def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    access_token = create_access_token({"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    user = await get_user(current_user.username)
    if not user:
        raise HTTPException(404, "User not found")
    return UserResponse(**{k: user[k] for k in ("username", "email", "created_at")})
