# app/services/auth_service.py

from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.config import Settings
from firebase_admin import auth as firebase_admin_auth
from app.firebase_client import FirebaseClient
import requests  # Added for REST API request

class AuthService:
    """Service for authentication related operations"""

    def __init__(self):
        self.settings = Settings()
        self.firebase_client = FirebaseClient()

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.settings.SECRET_KEY, algorithm=self.settings.ALGORITHM)
        return encoded_jwt

    def authenticate_user(self, email: str, password: str):
        """Authenticate a user with Firebase REST API"""
        try:
            # Payload to send to Firebase REST API
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }

            # Send request to Firebase REST API
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.settings.FIREBASE_API_KEY}",
                json=payload
            )

            if response.status_code == 200:
                user_info = response.json()
                user_id = user_info["localId"]
                user_data = self.firebase_client.get_user(user_id)
                return user_data
            else:
                return None
        except Exception as e:
            return None

    def verify_token(self, token: str):
        """Verify a JWT token"""
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=[self.settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except jwt.JWTError:
            return None
