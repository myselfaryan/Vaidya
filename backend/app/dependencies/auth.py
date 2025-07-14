"""
Authentication dependencies for FastAPI endpoints.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.models import User
from ..services.auth_service import auth_service


# Security scheme for JWT Bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: JWT credentials from Authorization header
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Get token from credentials
        token = credentials.credentials
        
        # Get user from token
        user = auth_service.get_current_user_from_token(db, token)
        
        if user is None:
            raise credentials_exception
            
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
            
        return user
        
    except Exception:
        raise credentials_exception


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current authenticated user from JWT token (optional).
    
    Args:
        credentials: JWT credentials from Authorization header (optional)
        db: Database session
        
    Returns:
        Current authenticated user or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        # Get token from credentials
        token = credentials.credentials
        
        # Get user from token
        user = auth_service.get_current_user_from_token(db, token)
        
        if user and user.is_active:
            return user
            
    except Exception:
        pass
    
    return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current verified user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Current verified user
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not verified"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get admin user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Admin user
        
    Raises:
        HTTPException: If user is not admin
    """
    from ..models.models import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_doctor_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get doctor user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        Doctor user
        
    Raises:
        HTTPException: If user is not doctor
    """
    from ..models.models import UserRole
    
    if current_user.role not in [UserRole.DOCTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor privileges required"
        )
    return current_user
