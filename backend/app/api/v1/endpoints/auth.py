"""
Authentication endpoints using OAuth2 with password flow.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import TokenResponse, LoginRequest
from app.services.auth_service import authenticate_user, create_access_and_refresh_tokens


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) - TokenResponse:
    """
    Authenticate user and return access and refresh tokens.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token, refresh_token = create_access_and_refresh_tokens(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    """
    # Implement refresh logic
    pass


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    """
    Logout user and invalidate tokens.
    """
    # Implement logout logic
    pass

