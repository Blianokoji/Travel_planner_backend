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

# Import your existing modules
from src.routes.auth import auth_router  # Updated import for FastAPI router
from src.utils.database import database
from src.services.planner import TravelPlanner

# Load environment variables
load_dotenv()

# Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'Dracalar@2099')  # Use env var for security
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours

MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://blessenprojects:EnBiva2qoqhsQg5u@cluster0.seoid.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize FastAPI app
app = FastAPI(
    title="Travel Planner API",
    description="API for generating travel plans",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-dot-weather-model-454711.el.r.appspot.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Database and services initialization
mongo_db = database.db
planner = TravelPlanner(
    gemini_api_key=GEMINI_API_KEY,
    google_maps_api_key=GOOGLE_MAPS_API_KEY
)

# Logging configuration
log_path = os.path.join('/tmp', 'fastapi_app.log')
if not os.path.exists('/tmp'):
    os.makedirs('/tmp')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_path)
    ]
)

# Pydantic models
class TravelPlanRequest(BaseModel):
    destination: str
    startDate: str
    endDate: str
    budget: str
    preferences: Optional[str] = ""

class TravelPlanResponse(BaseModel):
    plan: str

class TokenData(BaseModel):
    username: Optional[str] = None

# JWT utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

# Dependency for JWT authentication
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

# Include authentication router
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Routes
@app.get("/", tags=["root"])
async def read_root():
    return {"message": "Travel Planner API is running"}

@app.post("/generate_plan", response_model=TravelPlanResponse, tags=["travel"])
async def generate_plan(
    request: TravelPlanRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Generate a travel plan based on destination, dates, budget, and preferences.
    Requires JWT authentication.
    """
    try:
        logging.debug(f"Received data from frontend: {request.dict()}")
        
        # Call the travel planner service
        logging.info("Calling generate_travel_plan")
        plan = planner.generate_travel_plan(
            destination=request.destination,
            start_date=request.startDate,
            end_date=request.endDate,
            budget=request.budget,
            preferences=request.preferences
        )
        
        if plan is None:
            logging.error("Travel plan generation failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate plan due to internal error"
            )
        
        logging.info(f"Generated plan successfully for user: {current_user.username}")
        return TravelPlanResponse(plan=plan)
        
    except Exception as e:
        logging.error(f"Error generating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Travel Planner API"
    }

# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(KeyError)
async def key_error_handler(request, exc):
    return HTTPException(status_code=400, detail=f"Missing field: {str(exc)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:app",
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8000)),
        reload=True
    )