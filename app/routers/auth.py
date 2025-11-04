# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import Settings
from services.auth_service import AuthService
from firebase_client import FirebaseClient

router = APIRouter()
settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
auth_service = AuthService()
firebase_client = FirebaseClient()

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

#Get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = firebase_client.get_user(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

#Register user
@router.post("/register", response_model=Token)
async def register_user(user_data: UserCreate):
    # Check if email already exists
    try:
        # Create user and get user_id
        user_id = firebase_client.create_user(user_data.model_dump())
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": user_id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}"
        )

#Login
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_service.create_access_token(
            data={"sub": user["id"]}  
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

#Read users
@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user