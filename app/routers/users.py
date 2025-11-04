# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any
from datetime import datetime

from app.routers.auth import get_current_user
from app.firebase_client import FirebaseClient
from app.models.user import UserUpdate, UserResponse, FCMTokenUpdate, EmergencyContactUpdate , DependentsUpdate

router = APIRouter()
firebase_client = FirebaseClient()

# Get user profile by ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile_by_id(
    user_id: str = Path(..., description="The user's ID"),
    current_user=Depends(get_current_user)
):
    """Get a user's profile by user_id"""
    try:
        # Security check: only allow the user themselves or admins
        if user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to view this profile")

        user = firebase_client.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )

# Update user profile by ID
@router.put("/{user_id}", response_model=UserResponse)
async def update_user_profile_by_id(
    user_data: UserUpdate,
    user_id: str = Path(..., description="The user's ID"),
    current_user=Depends(get_current_user)
):
    """Update a user's profile by user_id"""
    try:
        if user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this profile")

        update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
        firebase_client.update_user(user_id, update_data)
        updated_user = firebase_client.get_user(user_id)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update user profile: {str(e)}"
        )

# Update user's dependents
@router.put("/{user_id}/dependents")
async def update_user_dependents(
    dependents_data: DependentsUpdate,
    user_id: str = Path(..., description="The user's ID"),
    current_user=Depends(get_current_user)
):
    """Update the user's dependents"""
    try:
        if user_id != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update dependents for this user")

        dependents = dependents_data.dependents
        firebase_client.update_user(user_id, {'dependents': dependents})
        return {"message": "Dependents updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update dependents: {str(e)}"
        )

@router.post("/fcm-token")
async def update_fcm_token(
    token_data: FCMTokenUpdate,
    current_user=Depends(get_current_user)
):
    """Update the user's FCM token for push notifications"""
    try:
        if not token_data.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FCM token is required"
            )
        firebase_client.update_user(current_user['id'], {'fcm_token': token_data.token})
        return {"message": "FCM token updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update FCM token: {str(e)}"
        )

@router.post("/emergency-contact")
async def update_emergency_contact(
    contact_data: EmergencyContactUpdate,
    current_user=Depends(get_current_user)
):
    """Update the user's emergency contact information"""
    try:
        firebase_client.update_user(current_user['id'], {'emergency_contact': contact_data.model_dump()})
        return {"message": "Emergency contact updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update emergency contact: {str(e)}"
        )

@router.get("/home-data")
async def get_home_data(current_user=Depends(get_current_user)):
    """Get data for the home page"""
    try:
        user = current_user
        upcoming_medications = firebase_client.get_upcoming_medications(user['id'], limit=3)
        upcoming_appointments = firebase_client.get_upcoming_appointments(user['id'], limit=1)
        next_appointment = upcoming_appointments[0] if upcoming_appointments else None
        medications = firebase_client.get_medications(user['id'])
        current_medications = [med for med in medications if not med.get('end_date') or med.get('end_date') > datetime.now()]
        
        latest_measurements = {}
        measurement_types = ["blood_pressure", "blood_sugar", "weight", "temperature", "heart_rate"]
        for m_type in measurement_types:
            measurements = firebase_client.get_measurements(
                user_id=user['id'],
                measurement_type=m_type,
                limit=1
            )
            if measurements:
                latest_measurements[m_type] = measurements[0]

        home_data = {
            "user_name": user.get('name'),
            "upcoming_medications": upcoming_medications,
            "next_appointment": next_appointment,
            "current_medications": current_medications[:5],
            "latest_measurements": latest_measurements
        }
        return home_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve home data: {str(e)}"
        )
