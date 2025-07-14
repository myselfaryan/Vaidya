"""
Authentication service for user management and JWT token handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from loguru import logger

from ..core.config import settings
from ..models.models import User, UserSession
from ..models.schemas import UserCreate, UserResponse


class AuthService:
    """Service for authentication and user management."""
    
    def __init__(self):
        """Initialize authentication service."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def create_user(self, db: Session, user: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user: User creation data
            
        Returns:
            Created user object
        """
        # Check if user already exists
        if self.get_user_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if self.get_user_by_username(db, user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = self.get_password_hash(user.password)
        
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            data_sharing_consent=user.data_sharing_consent,
            marketing_consent=user.marketing_consent
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created new user: {user.username}")
        return db_user
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = self.get_user_by_username(db, username)
        if not user:
            user = self.get_user_by_email(db, username)
        
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """
        Create JWT refresh token.
        
        Args:
            data: Token payload data
            
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            return None
    
    def create_user_session(
        self,
        db: Session,
        user_id: UUID,
        access_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str
    ) -> UserSession:
        """
        Create a new user session.
        
        Args:
            db: Database session
            user_id: User ID
            access_token: Access token
            refresh_token: Refresh token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Created user session
        """
        session = UserSession(
            user_id=user_id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def invalidate_session(self, db: Session, session_token: str) -> bool:
        """
        Invalidate a user session.
        
        Args:
            db: Database session
            session_token: Session token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        
        return False
    
    def refresh_access_token(self, db: Session, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Refresh access token using refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token
            
        Returns:
            New access and refresh tokens if valid, None otherwise
        """
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Check if session exists and is active
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        ).first()
        
        if not session:
            return None
        
        # Create new tokens
        access_token = self.create_access_token(data={"sub": user_id})
        new_refresh_token = self.create_refresh_token(data={"sub": user_id})
        
        # Update session
        session.session_token = access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        session.last_activity = datetime.utcnow()
        
        db.commit()
        
        return access_token, new_refresh_token
    
    def get_current_user_from_token(self, db: Session, token: str) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            db: Database session
            token: JWT token
            
        Returns:
            User object if valid, None otherwise
        """
        payload = self.verify_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user_uuid = UUID(user_id)
            return self.get_user_by_id(db, user_uuid)
        except (ValueError, TypeError):
            return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user - standalone function for backward compatibility.
    
    Args:
        db: Database session
        username: Username or email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    auth_service = AuthService()
    return auth_service.authenticate_user(db, username, password)


def create_access_and_refresh_tokens(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    """
    Create access and refresh tokens - standalone function for backward compatibility.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Tuple of (access_token, refresh_token)
    """
    auth_service = AuthService()
    access_token = auth_service.create_access_token(data, expires_delta)
    refresh_token = auth_service.create_refresh_token(data)
    return access_token, refresh_token


# Global auth service instance
auth_service = AuthService()
