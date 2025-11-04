# app/models/measurement.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, Any, Union
from datetime import datetime
import uuid


class MeasurementType(str, Enum):
    BLOOD_PRESSURE = "blood_pressure"
    BLOOD_SUGAR = "blood_sugar"
    WEIGHT = "weight"
    TEMPERATURE = "temperature"
    HEART_RATE = "heart_rate"


class BloodPressureData(BaseModel):
    systolic: int
    diastolic: int
    pulse: Optional[int] = None


class BloodSugarData(BaseModel):
    value: float
    unit: str = "mg/dL"  # Default unit (alternatives: mmol/L)
    measurement_context: Optional[str] = None  # e.g., "fasting", "after meal"


class MeasurementBase(BaseModel):
    type: str  # Using string to match your existing implementation
    value: Union[float, Dict[str, Any]]  # Can be a simple value or complex object like blood pressure
    unit: str
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    source: str = "manual"  # "manual" or "image_upload"


class MeasurementCreate(BaseModel):
    type: str
    value: Union[float, BloodPressureData, BloodSugarData]
    unit: str
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    source: str = "manual"
    status: Optional[str] = None


class MeasurementResponse(MeasurementBase):
    id: str
    created_at: Optional[datetime] = None


class MeasurementDB(BaseModel):
    """Helper class for converting between API models and Firebase storage"""
    
    @staticmethod
    def to_db_format(measurement: MeasurementBase, user_id: str) -> Dict[str, Any]:
        """Convert measurement model to Firebase database format"""
        measurement_data = measurement.model_dump()
        
        # Add additional fields for Firebase
        measurement_data["id"] = str(uuid.uuid4())
        measurement_data["user_id"] = user_id
        measurement_data["created_at"] = datetime.now()
        
        # Set timestamp to now if not provided
        if not measurement_data.get("timestamp"):
            measurement_data["timestamp"] = datetime.now()
        
        return measurement_data
    
    @staticmethod
    def from_blood_pressure_ocr(data: Dict[str, Any], user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a blood pressure measurement from OCR data"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "blood_pressure",
            "value": {
                "systolic": data["systolic"],
                "diastolic": data["diastolic"],
                "pulse": data.get("pulse")
            },
            "unit": "mmHg",
            "timestamp": datetime.now(),
            "notes": notes,
            "source": "image_upload",
            "created_at": datetime.now()
        }
    
    @staticmethod
    def from_blood_sugar_ocr(data: Dict[str, Any], user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Create a blood sugar measurement from OCR data"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "blood_sugar",
            "value": data["value"],
            "unit": data.get("unit", "mg/dL"),
            "timestamp": datetime.now(),
            "notes": notes,
            "source": "image_upload",
            "created_at": datetime.now()
        }