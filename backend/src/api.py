"""
FastAPI Web API for S3 Multipart Upload System
Provides REST endpoints for the frontend to interact with the backend services
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Load environment variables
try:
    from dotenv import load_dotenv
    # Get the backend directory (parent of src)
    backend_dir = os.path.dirname(os.path.dirname(__file__))
    production_env_path = os.path.join(backend_dir, 'production.env')
    env_path = os.path.join(backend_dir, '.env')
    
    # Try to load from production.env first, then fallback to .env
    if os.path.exists(production_env_path):
        load_dotenv(production_env_path, override=True)
        print("✅ Environment variables loaded from production.env")
        print(f"🔍 BUCKET_NAME: {os.getenv('BUCKET_NAME', 'NOT SET')}")
        print(f"🔍 COGNITO_USER_POOL_ID: {os.getenv('COGNITO_USER_POOL_ID', 'NOT SET')}")
    elif os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print("✅ Environment variables loaded from .env")
    else:
        print("⚠️ No environment file found, using system environment")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")

# Add src to path for imports
sys.path.append(os.path.dirname(__file__))

from upload.multipart_uploader import S3MultipartUploader
from security.file_validator import FileValidator
from monitoring.security_monitor import SecurityMonitor
from auth.cognito_auth import CognitoAuthService
from auth.dependencies import (
    get_current_user, require_upload_permission, require_view_permission,
    require_admin_permission, get_user_id, get_user_email, get_user_role
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app with metadata for Swagger UI
app = FastAPI(
    title="S3 Multipart Upload API",
    description="""
    Secure S3 multipart upload system with validation, monitoring, and security features.
    
    ## Features
    - **Multipart Upload**: Efficient large file uploads with resumable capability
    - **File Validation**: Comprehensive security and type validation
    - **Security Monitoring**: Real-time monitoring and threat detection
    - **Encryption**: Server-side encryption with KMS
    - **Access Control**: Role-based access with IAM integration
    
    ## Authentication
    This API uses AWS IAM credentials for authentication. Ensure your environment
    has the necessary AWS credentials configured.
    """,
    version="1.0.0",
    contact={
        "name": "Development Team",
        "email": "dev@company.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS configuration for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend services
try:
    uploader = S3MultipartUploader()
    validator = FileValidator()
    monitor = SecurityMonitor()
    auth_service = CognitoAuthService()
    logger.info("Backend services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize backend services: {e}")
    uploader = None
    validator = None
    monitor = None
    auth_service = None

# Pydantic models for request/response validation
class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status of the API")
    message: str = Field(..., description="Health status message")
    timestamp: str = Field(..., description="Current timestamp")
    services: Dict[str, str] = Field(..., description="Status of backend services")

class BucketTestRequest(BaseModel):
    bucket_name: str = Field(..., description="S3 bucket name to test")

class BucketTestResponse(BaseModel):
    accessible: bool = Field(..., description="Whether the bucket is accessible")
    message: str = Field(..., description="Test result message")
    bucket_name: str = Field(..., description="Bucket name that was tested")

class InitiateUploadRequest(BaseModel):
    file_key: str = Field(..., description="S3 object key for the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    metadata: Optional[Dict[str, str]] = Field(None, description="Additional metadata")

class InitiateUploadResponse(BaseModel):
    upload_id: str = Field(..., description="Multipart upload ID")
    file_key: str = Field(..., description="S3 object key")
    message: str = Field(..., description="Success message")

class PresignedUrlRequest(BaseModel):
    file_key: str = Field(..., description="S3 object key")
    upload_id: str = Field(..., description="Multipart upload ID")
    part_number: int = Field(..., description="Part number (1-based)")
    expiration: Optional[int] = Field(3600, description="URL expiration time in seconds")

class PresignedUrlResponse(BaseModel):
    presigned_url: str = Field(..., description="Presigned URL for uploading the part")
    part_number: int = Field(..., description="Part number")
    expires_in: int = Field(..., description="URL expiration time in seconds")

class UploadPart(BaseModel):
    part_number: int = Field(..., description="Part number")
    etag: str = Field(..., description="ETag of the uploaded part")

class CompleteUploadRequest(BaseModel):
    upload_id: str = Field(..., description="Multipart upload ID")
    file_key: str = Field(..., description="S3 object key")
    parts: List[UploadPart] = Field(..., description="List of uploaded parts")

class CompleteUploadResponse(BaseModel):
    success: bool = Field(..., description="Whether the upload was completed successfully")
    file_key: str = Field(..., description="S3 object key")
    file_url: str = Field(..., description="URL to access the uploaded file")
    message: str = Field(..., description="Success message")

class SecurityLogResponse(BaseModel):
    logs: List[Dict[str, Any]] = Field(..., description="Security log entries")
    total_entries: int = Field(..., description="Total number of log entries")
    query_timestamp: str = Field(..., description="Timestamp of the query")

# Authentication models
class RegisterRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    name: str = Field(..., description="User's full name")
    role: str = Field("uploader", description="User's role (admin, uploader, viewer)")

class LoginRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class ConfirmUserRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    confirmation_code: str = Field(..., description="Confirmation code from email")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class AuthResponse(BaseModel):
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    access_token: Optional[str] = Field(None, description="Access token")
    id_token: Optional[str] = Field(None, description="ID token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    token_type: Optional[str] = Field(None, description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")
    user: Optional[Dict[str, Any]] = Field(None, description="User information")

class UserInfoResponse(BaseModel):
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User's email")
    name: str = Field(..., description="User's name")
    role: str = Field(..., description="User's role")
    groups: List[str] = Field(..., description="User's groups")
    status: str = Field(..., description="User's status")

# API Routes

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information"""
    return {
        "name": "S3 Multipart Upload API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring API availability"""
    services_status = {
        "uploader": "available" if uploader else "unavailable",
        "validator": "available" if validator else "unavailable", 
        "monitor": "available" if monitor else "unavailable"
    }
    
    all_services_available = all(status == "available" for status in services_status.values())
    
    return HealthResponse(
        status="healthy" if all_services_available else "degraded",
        message="API is operational" if all_services_available else "Some services unavailable",
        timestamp=datetime.now().isoformat(),
        services=services_status
    )

# Authentication endpoints

@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest):
    """Register a new user"""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        result = auth_service.register_user(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role
        )
        
        return AuthResponse(
            success=result['success'],
            message=result['message'],
            user=result
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest):
    """Authenticate user and return tokens"""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        result = auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        return AuthResponse(
            success=result['success'],
            message="Login successful",
            access_token=result['access_token'],
            id_token=result['id_token'],
            refresh_token=result['refresh_token'],
            token_type=result['token_type'],
            expires_in=result['expires_in'],
            user=result['user']
        )
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/confirm", response_model=AuthResponse)
async def confirm_user(request: ConfirmUserRequest):
    """Confirm user registration with confirmation code"""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        result = auth_service.confirm_user(
            email=request.email,
            confirmation_code=request.confirmation_code
        )
        
        return AuthResponse(
            success=result['success'],
            message=result['message']
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"User confirmation failed: {e}")
        raise HTTPException(status_code=500, detail="Confirmation failed")

@app.post("/api/auth/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        result = auth_service.refresh_token(request.refresh_token)
        
        return AuthResponse(
            success=result['success'],
            message="Token refreshed successfully",
            access_token=result['access_token'],
            id_token=result['id_token'],
            token_type=result['token_type'],
            expires_in=result['expires_in']
        )
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@app.get("/api/auth/me", response_model=UserInfoResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return UserInfoResponse(
        user_id=current_user['user_id'],
        email=current_user['email'],
        name=current_user['name'],
        role=current_user['role'],
        groups=current_user['groups'],
        status=current_user.get('status', 'ACTIVE')
    )

@app.post("/api/auth/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout current user"""
    if not auth_service:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        # Note: In a real implementation, you'd need to pass the access token
        # For now, we'll just return success
        return {"success": True, "message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@app.post("/api/test-bucket", response_model=BucketTestResponse)
async def test_bucket_access(request: BucketTestRequest):
    """Test S3 bucket accessibility and permissions"""
    if not uploader:
        raise HTTPException(status_code=503, detail="Uploader service unavailable")
    
    try:
        # Test bucket access by trying to list objects (with max 1 result)
        uploader.s3_client.list_objects_v2(
            Bucket=request.bucket_name,
            MaxKeys=1
        )
        
        return BucketTestResponse(
            accessible=True,
            message=f"Bucket '{request.bucket_name}' is accessible",
            bucket_name=request.bucket_name
        )
    
    except Exception as e:
        logger.error(f"Bucket access test failed: {e}")
        return BucketTestResponse(
            accessible=False,
            message=f"Bucket access failed: {str(e)}",
            bucket_name=request.bucket_name
        )

@app.post("/api/upload/initiate", response_model=InitiateUploadResponse)
async def initiate_upload(
    request: InitiateUploadRequest,
    current_user: Dict[str, Any] = Depends(require_upload_permission)
):
    """Initiate a multipart upload for a file"""
    if not uploader:
        raise HTTPException(status_code=503, detail="Uploader service unavailable")
    
    try:
        # Validate file using the validator if available
        if validator:
            # Note: For API, we validate based on metadata since we don't have the file yet
            if request.file_size > validator.max_file_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File size exceeds maximum allowed size of {validator.max_file_size} bytes"
                )
        
        # Initiate multipart upload
        result = uploader.initiate_multipart_upload(
            file_key=request.file_key,
            metadata=request.metadata
        )
        
        # Log the initiation if monitor is available
        if monitor:
            monitor.log_upload_activity(
                user_id=current_user['user_id'],
                file_key=request.file_key,
                file_size=request.file_size,
                upload_status="initiated",
                metadata=request.metadata
            )
        
        return InitiateUploadResponse(
            upload_id=result["upload_id"],
            file_key=request.file_key,
            message="Multipart upload initiated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload initiation failed: {str(e)}")

@app.post("/api/upload/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    request: PresignedUrlRequest,
    current_user: Dict[str, Any] = Depends(require_upload_permission)
):
    """Generate a presigned URL for uploading a specific part"""
    if not uploader:
        raise HTTPException(status_code=503, detail="Uploader service unavailable")
    
    try:
        presigned_url = uploader.generate_presigned_url(
            file_key=request.file_key,
            upload_id=request.upload_id,
            part_number=request.part_number,
            expires_in=request.expiration
        )
        
        return PresignedUrlResponse(
            presigned_url=presigned_url,
            part_number=request.part_number,
            expires_in=request.expiration
        )
    
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(status_code=500, detail=f"Presigned URL generation failed: {str(e)}")

@app.post("/api/upload/complete", response_model=CompleteUploadResponse)
async def complete_upload(
    request: CompleteUploadRequest,
    current_user: Dict[str, Any] = Depends(require_upload_permission)
):
    """Complete a multipart upload"""
    if not uploader:
        raise HTTPException(status_code=503, detail="Uploader service unavailable")
    
    try:
        # Convert parts to the format expected by the backend
        parts_list = [
            {"PartNumber": part.part_number, "ETag": part.etag}
            for part in request.parts
        ]
        
        result = uploader.complete_multipart_upload(
            file_key=request.file_key,
            upload_id=request.upload_id,
            parts=parts_list
        )
        
        # Log completion if monitor is available
        if monitor:
            monitor.log_upload_activity(
                user_id=current_user['user_id'],
                file_key=request.file_key,
                file_size=0,  # We don't have file size here
                upload_status="completed"
            )
        
        # Generate file URL (simplified)
        file_url = f"s3://{uploader.bucket_name}/{request.file_key}"
        
        return CompleteUploadResponse(
            success=True,
            file_key=request.file_key,
            file_url=file_url,
            message="File uploaded successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to complete upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload completion failed: {str(e)}")

@app.get("/api/security/logs", response_model=SecurityLogResponse)
async def get_security_logs(
    limit: int = 50, 
    hours: int = 24,
    current_user: Dict[str, Any] = Depends(require_admin_permission)
):
    """Retrieve security logs from CloudWatch"""
    if not monitor:
        raise HTTPException(status_code=503, detail="Security monitor unavailable")
    
    try:
        # Get logs from the monitor
        logs = monitor.get_recent_logs(hours=hours, limit=limit)
        
        return SecurityLogResponse(
            logs=logs,
            total_entries=len(logs),
            query_timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve security logs: {e}")
        raise HTTPException(status_code=500, detail=f"Log retrieval failed: {str(e)}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error occurred",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed")
    
    # Run the API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )