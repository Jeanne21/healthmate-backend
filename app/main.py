# app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import users, medications, appointments, measurements, auth, reports
from config import Settings
from dotenv import load_dotenv
import os
import logging

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Now you can access the environment variables
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
print(f"FIREBASE_CREDENTIALS_PATH: {firebase_credentials_path}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Health Tracker API",
    description="Backend API for Health Tracking Application",
    version="1.0.0"
)

# Load settings
settings = Settings()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:19006",  # React Native Expo default
    "*"  # For development purposes - restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(measurements.router, prefix="/api/measurements", tags=["Measurements"])
# Add the new reports router
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/")
async def root():
    return {"message": "Welcome to Health Tracker API. See /docs for API documentation."}

@app.get("/api/status")
async def status():
    return {
        "status": "operational",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)