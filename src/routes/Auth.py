from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime
from passlib.context import CryptContext
from src.models.firebase import firebase_db
from src.dependencies.auth import get_current_user, TokenData, create_access_token
import logging
from settings import settings
auth_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models 
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

class RegisterResponse(BaseModel):
    message: str
    user: UserResponse
    token: Token

# Helpers 
def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(username: str):
    if not firebase_db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    logging.debug(f"Querying user: {username}")
    docs = firebase_db.collection("users").where("username", "==", username).stream()
    for doc in docs:
        user = doc.to_dict()
        logging.debug(f"Found user: {user}")
        return user
    logging.debug(f"User not found: {username}")
    return None

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user or not verify_password(password, user["password"]):
        return None
    return user

# Routes 
@auth_router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(user: UserCreate, response: Response):
    try:
        if not firebase_db:
            raise HTTPException(status_code=503, detail="Database not available")
            
        if await get_user(user.username):
            raise HTTPException(400, "Username already exists")

        email_check = firebase_db.collection("users").where("email", "==", user.email).stream()
        for _ in email_check:
            raise HTTPException(400, "Email already registered")

        hashed_password = get_password_hash(user.password)
        data = {
            "username": user.username,
            "email": user.email,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        }
        logging.debug(f"Registering user: {data}")
        firebase_db.collection("users").add(data)
        
        # Generate token and set cookie
        access_token = create_access_token({"sub": user.username})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * settings.jwt_expire_minutes,
            path="/"
        )
        
        return RegisterResponse(
            message="Registration successful",
            user=UserResponse(**{k: data[k] for k in ("username", "email", "created_at")}),
            token=Token(access_token=access_token, token_type="bearer")
        )
    except Exception as e:
        logging.error(f"Error in register endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")

@auth_router.post("/login", response_model=Token)
async def login(user_data: UserLogin, response: Response):
    user = await authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    access_token = create_access_token({"sub": user["username"]})
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,            
        samesite="Lax",
        max_age=60 * settings.jwt_expire_minutes,
        path="/"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    logging.debug(f"Fetching user for username: {current_user.username}")
    user = await get_user(current_user.username)
    if not user:
        logging.debug(f"User not found: {current_user.username}")
        raise HTTPException(404, "User not found")
    return UserResponse(**{k: user[k] for k in ("username", "email", "created_at")})

@auth_router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("access_token")
    return response