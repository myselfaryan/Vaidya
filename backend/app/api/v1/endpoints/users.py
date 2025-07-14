"""
User management endpoints for registration, profile management, and user operations.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from loguru import logger

from app.core.database import get_db
from app.models.schemas import (
    UserCreate, UserResponse, UserProfile, UserUpdate,
    PaginatedResponse, PaginationParams
)
from app.models.models import User
from app.services.auth_service import auth_service
from app.dependencies.auth import get_current_user, get_admin_user


router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Register a new user account.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information
    """
    try:
        # Create new user
        user = auth_service.create_user(db, user_data)
        
        logger.info(f"User registered successfully: {user.email}")
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserProfile:
    """
    Get current user's profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile information
    """
    try:
        # Note: In a real implementation, you would decrypt medical information
        # For now, we'll return empty lists
        profile = UserProfile.from_orm(current_user)
        profile.medical_conditions = []
        profile.medications = []
        profile.allergies = []
        
        return profile
        
    except Exception as e:
        logger.error(f"Failed to get user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile information.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    try:
        # Update user fields
        if user_update.first_name is not None:
            current_user.first_name = user_update.first_name
        
        if user_update.last_name is not None:
            current_user.last_name = user_update.last_name
        
        if user_update.phone_number is not None:
            current_user.phone_number = user_update.phone_number
        
        if user_update.data_sharing_consent is not None:
            current_user.data_sharing_consent = user_update.data_sharing_consent
        
        if user_update.marketing_consent is not None:
            current_user.marketing_consent = user_update.marketing_consent
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User profile updated: {current_user.email}")
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"Failed to update user profile: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/me/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's usage statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User statistics
    """
    try:
        from app.services.conversation_service import conversation_service
        
        stats = conversation_service.get_user_conversation_stats(db, current_user.id)
        
        return {
            "user_id": current_user.id,
            "member_since": current_user.created_at,
            "last_login": current_user.last_login,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account (soft delete).
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        # Soft delete user account
        current_user.is_active = False
        db.commit()
        
        logger.info(f"User account deleted: {current_user.email}")
        return {"message": "User account deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete user account: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )


# Admin-only endpoints
@router.get("/", response_model=PaginatedResponse)
async def get_users(
    pagination: PaginationParams = Depends(),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> PaginatedResponse:
    """
    Get all users with pagination (admin only).
    
    Args:
        pagination: Pagination parameters
        admin_user: Admin user
        db: Database session
        
    Returns:
        Paginated list of users
    """
    try:
        # Get total count
        total = db.query(User).count()
        
        # Get users with pagination
        users = db.query(User).offset(
            (pagination.page - 1) * pagination.size
        ).limit(pagination.size).all()
        
        user_responses = [UserResponse.from_orm(user) for user in users]
        
        return PaginatedResponse(
            items=user_responses,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get user by ID (admin only).
    
    Args:
        user_id: User ID
        admin_user: Admin user
        db: Database session
        
    Returns:
        User information
    """
    try:
        from uuid import UUID
        
        user_uuid = UUID(user_id)
        user = auth_service.get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@router.put("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account (admin only).
    
    Args:
        user_id: User ID
        admin_user: Admin user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        from uuid import UUID
        
        user_uuid = UUID(user_id)
        user = auth_service.get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        db.commit()
        
        logger.info(f"User deactivated by admin: {user.email}")
        return {"message": "User account deactivated successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.put("/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate a user account (admin only).
    
    Args:
        user_id: User ID
        admin_user: Admin user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        from uuid import UUID
        
        user_uuid = UUID(user_id)
        user = auth_service.get_user_by_id(db, user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        db.commit()
        
        logger.info(f"User activated by admin: {user.email}")
        return {"message": "User account activated successfully"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate user: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )
