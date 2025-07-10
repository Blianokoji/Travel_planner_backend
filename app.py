from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import logging
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv
from src.dependencies.auth import get_current_user, TokenData
from src.routes.Auth import auth_router
from src.services.planner import TravelPlanner
from settings import settings

load_dotenv()

app = FastAPI(
    title=settings.app_name,
    description="API for generating travel plans",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

planner = TravelPlanner(
    gemini_api_key=settings.gemini_api_key,
    google_maps_api_key=settings.google_maps_api_key
)

log_path = settings.log_file
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path)
    ]
)

class TravelPlanRequest(BaseModel):
    destination: str
    startDate: str
    endDate: str
    budget: str
    preferences: Optional[str] = ""

from pydantic import BaseModel
from typing import Union

class TravelPlanResponse(BaseModel):
    plan: Union[str, dict]  # Or better: define the full plan schema


class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        return TokenData(username=username)
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Travel Planner API is running"}

@app.post("/generate_plan", response_model=TravelPlanResponse, tags=["travel"])
async def generate_plan(request: TravelPlanRequest, current_user: TokenData = Depends(get_current_user)):
    try:
        logging.debug(f"Received plan request: {request.dict()}")
        plan = planner.generate_travel_plan(
            destination=request.destination,
            start_date=request.startDate,
            end_date=request.endDate,
            budget=request.budget,
            preferences=request.preferences
        )
        if not plan:
            raise HTTPException(status_code=500, detail="Failed to generate plan")
        return TravelPlanResponse(plan=plan)
    except Exception as e:
        logging.error(f"Plan generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Travel Planner API"
    }
