# -----------------------------------------------------------------------------
# File: utils.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Authentication utilities (JWT, password hashing)
# -----------------------------------------------------------------------------

"""
Authentication utilities
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import os
import structlog
import bcrypt

logger = structlog.get_logger()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Increased from 30 to 120 minutes (2 hours)
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing - use bcrypt directly to avoid passlib compatibility issues
# Note: We removed passlib dependency due to bcrypt compatibility issues

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        # Ensure password is not too long (bcrypt limit is 72 bytes)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Use bcrypt directly
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        logger.error("password_verification_failed", error=str(e))
        return False

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Ensure password is not too long (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Use bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("token_decode_failed", error=str(e))
        return None

def get_current_user_from_token(token: str) -> Optional[Dict]:
    """Get user info from token"""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None





