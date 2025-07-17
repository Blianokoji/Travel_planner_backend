from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from src.dependencies.auth import get_current_user, TokenData
from src.services.planner import TravelPlanner
from src.routes.Auth import auth_router
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
    allow_methods=["*"],
    allow_headers=["*"],
)

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

app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Travel Planner API is running"}

class Activity(BaseModel):
    time: str
    description: str

class Day(BaseModel):
    date: str
    activities: List[Activity]

class TravelPlanResponse(BaseModel):
    title: str
    budget: float
    days: List[Day]
    notes: List[str]

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
        logging.debug(f"Generated plan: {plan}")
        return plan
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