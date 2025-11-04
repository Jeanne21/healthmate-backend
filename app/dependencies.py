# app/dependencies.py
from fastapi import Depends, HTTPException, status, Header
from typing import Optional
import logging
from firebase_client import FirebaseClient

logger = logging.getLogger(__name__)
firebase_client = FirebaseClient()

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get the current user from the Firebase ID token in the Authorization header.
    
    Args:
        authorization: The Authorization header value (Bearer token)
        
    Returns:
        dict: User data
        
    Raises:
        HTTPException: If the token is missing or invalid
    """

    logger.info(f"Authorization header: {authorization}")

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Extract token from "Bearer {token}"
        token = authorization.split(" ")[1] if " " in authorization else authorization
        
        # Verify the token
        user = firebase_client.verify_id_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except IndexError:
        # Malformed Authorization header
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer {token}'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )