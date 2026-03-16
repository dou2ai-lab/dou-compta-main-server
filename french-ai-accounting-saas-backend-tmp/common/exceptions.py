# -----------------------------------------------------------------------------
# File: exceptions.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Custom exception classes for error handling across the application
# -----------------------------------------------------------------------------

"""
Custom exceptions
Phase 1 - Placeholder
"""
from fastapi import HTTPException, status

class DouException(HTTPException):
    """Base exception for Dou Expense & Audit AI"""
    pass

class ValidationError(DouException):
    """Validation error"""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": message,
                "field": field
            }
        )

class AuthenticationError(DouException):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTHENTICATION_ERROR",
                "message": message
            }
        )

class AuthorizationError(DouException):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "AUTHORIZATION_ERROR",
                "message": message
            }
        )

class NotFoundError(DouException):
    """Resource not found error"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"{resource} not found"
            }
        )









