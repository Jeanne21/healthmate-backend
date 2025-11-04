# app/routers/measurements.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime, timedelta, timezone
import io
import traceback

from routers.auth import get_current_user
from firebase_client import FirebaseClient
from models.measurement import MeasurementBase, MeasurementCreate, MeasurementResponse, MeasurementDB
from utils.ocr_processor import OCRProcessor
from anomaly_predictor_tf import load_model, predict_anomaly

router = APIRouter()
firebase_client = FirebaseClient()
ocr_processor = OCRProcessor()

# Load both models once at startup
bp_model = load_model("models/bp_model_tf.h5")
diabetes_model = load_model("models/diabetes_model_tf.h5")

class MeasurementInput(BaseModel):
    user_id: str
    type: str
    value: dict  # could be nested for blood_pressure
    unit: str

@router.get("/", response_model=List[MeasurementResponse])
async def get_measurements(
    measurement_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user = Depends(get_current_user)
):
    """Get health measurements for the current user with optional filtering"""
    try:
        # Convert input strings to timezone-aware datetimes
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        if start_datetime.tzinfo is None:
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)

        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
        if end_datetime.tzinfo is None:
            end_datetime = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
        
        # Use the existing Firebase client method
        measurements = firebase_client.get_measurements(
            user_id=current_user['id'], 
            measurement_type=measurement_type,
            limit=limit
        )
        
        # Apply additional date filtering if needed (in case Firebase client doesn't support it)
        if start_datetime or end_datetime:
            filtered_measurements = []
            for m in measurements:
                m_timestamp = m.get('timestamp')

                # Convert string timestamp to datetime if needed
                if isinstance(m_timestamp, str):
                    m_timestamp = datetime.fromisoformat(m_timestamp.replace('Z', '+00:00'))

                # Ensure m_timestamp is timezone-aware
                if m_timestamp.tzinfo is None:
                    m_timestamp = m_timestamp.replace(tzinfo=timezone.utc)

                # Apply filters
                if start_datetime and m_timestamp < start_datetime:
                    continue
                if end_datetime and m_timestamp > end_datetime:
                    continue

                filtered_measurements.append(m)
                print("Filtered out timestamp:", m_timestamp.isoformat())

            return filtered_measurements
        
        return measurements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve measurements: {str(e)}"
        )

@router.get("/latest", response_model=Dict[str, MeasurementResponse])
async def get_latest_measurements(current_user = Depends(get_current_user)):
    """Get latest measurements of each type for the current user"""
    try:
        # Define measurement types
        measurement_types = ["blood_pressure", "blood_sugar", "weight", "temperature", "heart_rate"]
        
        latest_measurements = {}
        
        for m_type in measurement_types:
            measurements = firebase_client.get_measurements(
                user_id=current_user['id'],
                measurement_type=m_type,
                limit=1
            )
            
            if measurements and len(measurements) > 0:
                latest_measurements[m_type] = measurements[0]
        
        return latest_measurements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve latest measurements: {str(e)}"
        )

@router.post("/", response_model=MeasurementResponse)
async def create_measurement(
    measurement: MeasurementCreate,
    current_user = Depends(get_current_user)
):
    print("Received measurement data:", measurement)
    """Create a new health measurement for the current user"""
    try:
         # Get user profile for AI input
        user_profile = current_user

        # Convert Pydantic object to dict
        # measurement_dict = measurement.dict()

        # Predict anomaly using model
        if measurement.type == "blood_pressure":
            is_anomaly, msg = predict_anomaly(user_profile, measurement, bp_model, "blood_pressure")

        elif measurement.type == "blood_sugar":
            is_anomaly, msg = predict_anomaly(user_profile, measurement, diabetes_model, "diabetes")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported measurement type: {measurement.type}"
            )

        # Add status field to measurement data
        measurement.status = "anomaly" if is_anomaly else "normal"
        
        # Convert to DB format and store
        measurement_data = MeasurementDB.to_db_format(measurement, current_user['id'])
        
        # Add the measurement using existing firebase client
        measurement_id = firebase_client.add_measurement(current_user['id'], measurement_data)
        
        # Return the created measurement
        measurements = firebase_client.get_measurements(current_user['id'])
        for m in measurements:
            if m.get('id') == measurement_id:
                return m
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Measurement created but could not be retrieved"
        )
    except Exception as e:
        print("Error during measurement creation:")
        traceback.print_exc()  # Logs full stack trace to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create measurement: {str(e)}"
        )

@router.post("/upload", response_model=MeasurementResponse)
async def upload_measurement_image(
    measurement_type: str = Form(...),
    image: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """Process an uploaded image to extract and save measurement data"""
    # Validate measurement type
    valid_types = ["blood_pressure", "blood_sugar"]
    if measurement_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid measurement type for image upload. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        # Read image file
        contents = await image.read()
        
        # Process image with OCR
        extracted_data = ocr_processor.process_image(contents, measurement_type)
        
        # Create measurement based on type
        if measurement_type == "blood_pressure":
            measurement_data = MeasurementDB.from_blood_pressure_ocr(
                data=extracted_data, 
                user_id=current_user['id'],
                notes=notes
            )
        else:  # Blood sugar
            measurement_data = MeasurementDB.from_blood_sugar_ocr(
                data=extracted_data, 
                user_id=current_user['id'],
                notes=notes
            )
        
        # Save to Firebase
        measurement_id = firebase_client.add_measurement(current_user['id'], measurement_data)
        
        # Get the saved measurement
        measurements = firebase_client.get_measurements(current_user['id'])
        saved_measurement = next((m for m in measurements if m.get('id') == measurement_id), None)
        
        if not saved_measurement:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Measurement created but could not be retrieved"
            )
        
        return {
            **saved_measurement,
            "extracted_data": extracted_data  # Include the raw extracted data for reference
        }
        
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )

@router.get("/blood-pressure", response_model=List[MeasurementResponse])
async def get_blood_pressure(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user = Depends(get_current_user)
):
    """Get blood pressure measurements for the current user"""
    try:
        measurements = firebase_client.get_measurements(
            user_id=current_user['id'],
            measurement_type="blood_pressure",
            limit=limit
        )
        return measurements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve blood pressure measurements: {str(e)}"
        )

@router.get("/blood-sugar", response_model=List[MeasurementResponse])
async def get_blood_sugar(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    current_user = Depends(get_current_user)
):
    """Get blood sugar measurements for the current user"""
    try:
        measurements = firebase_client.get_measurements(
            user_id=current_user['id'],
            measurement_type="blood_sugar",
            limit=limit
        )
        return measurements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve blood sugar measurements: {str(e)}"
        )

@router.get("/stats/blood-pressure", response_model=Dict[str, Any])
async def get_blood_pressure_stats(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get statistical data about blood pressure measurements"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get measurements
        measurements = firebase_client.get_measurements(
            user_id=current_user['id'],
            measurement_type="blood_pressure"
        )
        
        # Filter by date range
        filtered_measurements = []
        for m in measurements:
            timestamp = m.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if start_date <= timestamp <= end_date:
                filtered_measurements.append(m)
        
        # Extract values
        systolic_values = []
        diastolic_values = []
        pulse_values = []
        
        for m in filtered_measurements:
            value = m.get('value', {})
            
            # Handle different data structures
            if isinstance(value, dict):
                # Complex object format
                if 'systolic' in value:
                    systolic_values.append(value['systolic'])
                if 'diastolic' in value:
                    diastolic_values.append(value['diastolic'])
                if 'pulse' in value:
                    pulse_values.append(value['pulse'])
            else:
                # If value is stored in a different format, try to extract from top level
                if 'systolic' in m:
                    systolic_values.append(m['systolic'])
                if 'diastolic' in m:
                    diastolic_values.append(m['diastolic'])
                if 'pulse' in m:
                    pulse_values.append(m['pulse'])
        
        # Calculate statistics
        stats = {
            "count": len(filtered_measurements),
            "period_days": days,
            "systolic": {
                "avg": sum(systolic_values) / len(systolic_values) if systolic_values else None,
                "min": min(systolic_values) if systolic_values else None,
                "max": max(systolic_values) if systolic_values else None
            },
            "diastolic": {
                "avg": sum(diastolic_values) / len(diastolic_values) if diastolic_values else None,
                "min": min(diastolic_values) if diastolic_values else None,
                "max": max(diastolic_values) if diastolic_values else None
            }
        }
        
        if pulse_values:
            stats["pulse"] = {
                "avg": sum(pulse_values) / len(pulse_values),
                "min": min(pulse_values),
                "max": max(pulse_values)
            }
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate blood pressure statistics: {str(e)}"
        )

@router.get("/stats/blood-sugar", response_model=Dict[str, Any])
async def get_blood_sugar_stats(
    days: int = 30,
    current_user = Depends(get_current_user)
):
    """Get statistical data about blood sugar measurements"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get measurements
        measurements = firebase_client.get_measurements(
            user_id=current_user['id'],
            measurement_type="blood_sugar"
        )
        
        # Filter by date range
        filtered_measurements = []
        for m in measurements:
            timestamp = m.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if start_date <= timestamp <= end_date:
                filtered_measurements.append(m)
        
        # Extract values and group by context
        all_values = []
        context_groups = {}
        
        for m in filtered_measurements:
            # Extract value based on structure
            value = None
            if isinstance(m.get('value'), dict) and 'value' in m['value']:
                value = m['value']['value']  # Nested value
            elif isinstance(m.get('value'), (int, float)):
                value = m['value']  # Direct value
            elif 'blood_sugar_value' in m:
                value = m['blood_sugar_value']  # Flattened value
            
            if value is not None:
                all_values.append(value)
                
                # Group by context if available
                context = None
                
                # Try to find context in different possible locations
                if isinstance(m.get('value'), dict) and 'measurement_context' in m['value']:
                    context = m['value']['measurement_context']
                elif 'measurement_context' in m:
                    context = m['measurement_context']
                elif 'notes' in m and m['notes']:
                    # Try to infer context from notes
                    lower_notes = m['notes'].lower()
                    if any(term in lower_notes for term in ['fast', 'before meal', 'before breakfast']):
                        context = 'fasting'
                    elif any(term in lower_notes for term in ['after meal', 'post', 'post meal']):
                        context = 'after meal'
                
                context = context or 'unknown'
                
                if context not in context_groups:
                    context_groups[context] = []
                context_groups[context].append(value)
        
        # Calculate statistics
        stats = {
            "count": len(filtered_measurements),
            "period_days": days,
            "overall": {
                "avg": sum(all_values) / len(all_values) if all_values else None,
                "min": min(all_values) if all_values else None,
                "max": max(all_values) if all_values else None
            },
            "by_context": {}
        }
        
        # Add context-specific stats
        for context, values in context_groups.items():
            stats["by_context"][context] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate blood sugar statistics: {str(e)}"
        )

@router.delete("/{measurement_id}")
async def delete_measurement(
    measurement_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a health measurement for the current user"""
    try:
        # Check if the measurement exists and belongs to the user
        measurements = firebase_client.get_measurements(current_user['id'])
        measurement = next((m for m in measurements if m.get('id') == measurement_id), None)
        
        if not measurement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Measurement not found"
            )
        
        # Delete the measurement
        result = firebase_client.db.collection('users').document(current_user['id']).collection('measurements').document(measurement_id).delete()
        
        return {"message": "Measurement deleted successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete measurement: {str(e)}"
        )
    
# @router.post("/check-anomaly/")
# async def check_anomaly(measurement: MeasurementInput, current_user = Depends(get_current_user)):
#        # Fetch user data from Firebase or internal DB
#        user = firebase_client.get_user(current_user['id'])
#        if not user:
#            raise HTTPException(status_code=404, detail="User not found")

#        is_anomalous, message = detect_anomaly(user, measurement.dict())
#        return {
#            "anomaly": is_anomalous,
#            "message": message
#        }

    # def fetch_user_from_firebase(user_id):
    # # Pseudocode: Use Firebase Admin SDK
    # import firebase_admin
    # from firebase_admin import firestore

    # db = firestore.client()
    # doc = db.collection("users").document(user_id).get()
    # if doc.exists:
    #     return doc.to_dict()
    # return None