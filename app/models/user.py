# app/models/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO format: YYYY-MM-DD
    blood_type: Optional[str] = None
    height: Optional[float] = None  # in cm or as needed
    weight: Optional[float] = None  # in kg or as needed
    
    fcm_token: Optional[str] = None
    emergency_contact: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    blood_type: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    emergency_contact: Optional[Dict[str, Any]] = None

class DependentsUpdate(BaseModel):
    dependents: List[Dict[str, Any]]

class FCMTokenUpdate(BaseModel):
    token: str

class EmergencyContactUpdate(BaseModel):
    name: str
    phone: str
    relationship: Optional[str] = None  # Can be optional if desired
