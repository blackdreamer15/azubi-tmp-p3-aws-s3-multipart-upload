"""
FastAPI Dependencies for Authentication
Provides authentication and authorization dependencies for API endpoints
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .cognito_auth import CognitoAuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Global auth service instance
auth_service = None

def get_auth_service() -> CognitoAuthService:
    """Get or create the authentication service instance"""
    global auth_service
    if auth_service is None:
        try:
            auth_service = CognitoAuthService()
        except Exception as e:
            logger.error(f"Failed to initialize auth service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )
    return auth_service

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Cognito authentication service
    Returns:
        Dictionary containing user information
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        validation_result = auth_service.validate_token(token)

        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_info = validation_result['user']
        logger.info(f"Authenticated user: {user_info['email']}")

        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def require_permission(
    permission: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """
    Require specific permission for the current user
    Args:
        permission: Required permission (upload, view, admin, delete)
        current_user: Current authenticated user
        auth_service: Cognito authentication service
    Returns:
        Dictionary containing user information
    Raises:
        HTTPException: If user doesn't have required permission
    """
    if not auth_service.check_permission(current_user, permission):
        logger.warning(f"Access denied for user {current_user['email']} - required permission: {permission}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {permission}"
        )

    return current_user

# Specific permission dependencies
def require_upload_permission(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require upload permission"""
    if not auth_service.check_permission(current_user, "upload"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: upload"
        )
    return current_user

def require_view_permission(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require view permission"""
    if not auth_service.check_permission(current_user, "view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: view"
        )
    return current_user

def require_admin_permission(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require admin permission"""
    if not auth_service.check_permission(current_user, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: admin"
        )
    return current_user

def require_delete_permission(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Require delete permission"""
    if not auth_service.check_permission(current_user, "delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Required: delete"
        )
    return current_user

# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: CognitoAuthService = Depends(get_auth_service)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None
    Args:
        credentials: Optional HTTP Bearer token credentials
        auth_service: Cognito authentication service
    Returns:
        Dictionary containing user information or None if not authenticated
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        validation_result = auth_service.validate_token(token)

        if validation_result['valid']:
            return validation_result['user']
        else:
            return None

    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None

def get_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Extract user ID from current user
    Args:
        current_user: Current authenticated user
    Returns:
        User ID string
    """
    return current_user.get('user_id', '')

def get_user_email(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Extract user email from current user
    Args:
        current_user: Current authenticated user
    Returns:
        User email string
    """
    return current_user.get('email', '')

def get_user_role(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Extract user role from current user
    Args:
        current_user: Current authenticated user
    Returns:
        User role string
    """
    return current_user.get('role', 'viewer')
