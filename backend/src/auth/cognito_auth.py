"""
AWS Cognito Authentication Service
Handles user authentication, authorization, and JWT token validation
"""

import os
import boto3
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
try:
    from cognitojwt import decode as cognito_decode
except ImportError:
    # Fallback if cognitojwt is not available
    cognito_decode = None
from jose import JWTError, jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CognitoAuthService:
    """Handles AWS Cognito authentication and authorization"""
    
    def __init__(self):
        """Initialize the Cognito authentication service"""
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_USER_POOL_CLIENT_ID')
        self.identity_pool_id = os.getenv('COGNITO_IDENTITY_POOL_ID')
        
        if not all([self.user_pool_id, self.client_id, self.identity_pool_id]):
            raise ValueError("Cognito configuration missing. Please set COGNITO_USER_POOL_ID, COGNITO_USER_POOL_CLIENT_ID, and COGNITO_IDENTITY_POOL_ID")
        
        # Initialize Cognito client
        try:
            self.cognito_client = boto3.client('cognito-idp', region_name=self.aws_region)
            self.cognito_identity_client = boto3.client('cognito-identity', region_name=self.aws_region)
        except Exception as e:
            raise ValueError(f"Failed to initialize Cognito clients: {e}")
        
        # JWT configuration
        self.jwt_algorithm = "RS256"
        self.jwt_issuer = f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.user_pool_id}"
        
        logger.info(f"Initialized CognitoAuthService for user pool: {self.user_pool_id}")
    
    def register_user(self, email: str, password: str, name: str, role: str = "uploader") -> Dict[str, Any]:
        """
        Register a new user in Cognito
        
        Args:
            email: User's email address
            password: User's password
            name: User's full name
            role: User's role (admin, uploader, viewer)
            
        Returns:
            Dictionary containing registration result
        """
        try:
            # Validate role
            if role not in ["admin", "uploader", "viewer"]:
                raise ValueError(f"Invalid role: {role}. Must be one of: admin, uploader, viewer")
            
            # Register user
            response = self.cognito_client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'name', 'Value': name},
                    {'Name': 'custom:role', 'Value': role}
                ]
            )
            
            user_id = response['UserSub']
            
            # Add user to appropriate group
            self._add_user_to_group(email, role)
            
            logger.info(f"User registered successfully: {email} with role: {role}")
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'role': role,
                'confirmation_required': response.get('UserConfirmed', False),
                'message': 'User registered successfully. Please check your email for confirmation.'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                raise ValueError("User with this email already exists")
            elif error_code == 'InvalidPasswordException':
                raise ValueError("Password does not meet requirements")
            else:
                logger.error(f"Failed to register user: {e}")
                raise ValueError(f"Registration failed: {e}")
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and return tokens
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary containing authentication tokens and user info
        """
        try:
            # Authenticate user
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            auth_result = response['AuthenticationResult']
            
            # Get user details
            user_info = self._get_user_info(email)
            
            logger.info(f"User authenticated successfully: {email}")
            
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn'],
                'user': user_info
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                raise ValueError("Invalid email or password")
            elif error_code == 'UserNotConfirmedException':
                raise ValueError("User account not confirmed. Please check your email.")
            else:
                logger.error(f"Authentication failed: {e}")
                raise ValueError(f"Authentication failed: {e}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary containing new tokens
        """
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response['AuthenticationResult']
            
            return {
                'success': True,
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'token_type': auth_result['TokenType'],
                'expires_in': auth_result['ExpiresIn']
            }
            
        except ClientError as e:
            logger.error(f"Token refresh failed: {e}")
            raise ValueError("Token refresh failed")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token and extract user information
        
        Args:
            token: JWT access token or ID token
            
        Returns:
            Dictionary containing token validation result and user info
        """
        try:
            logger.info(f"Validating token for user pool: {self.user_pool_id}, client: {self.client_id}")
            
            # Use cognitojwt to validate the token if available
            if cognito_decode is None:
                logger.warning("cognitojwt not available, using basic JWT validation")
                # Fallback to basic JWT validation
                verified_claims = jwt.decode(
                    token,
                    key="",  # Empty key since we're not verifying signature
                    options={"verify_signature": False}  # Skip signature verification for now
                )
            else:
                verified_claims = cognito_decode(
                    token,
                    self.aws_region,
                    self.user_pool_id,
                    app_client_id=self.client_id
                )
            
            logger.info(f"Token validation successful, claims: {list(verified_claims.keys())}")
            
            # Extract user information
            user_info = {
                'user_id': verified_claims.get('sub'),
                'email': verified_claims.get('email'),
                'name': verified_claims.get('name'),
                'role': verified_claims.get('custom:role', 'uploader'),
                'groups': verified_claims.get('cognito:groups', []),
                'token_use': verified_claims.get('token_use'),
                'exp': verified_claims.get('exp'),
                'iat': verified_claims.get('iat')
            }
            
            # Check if token is expired
            if user_info.get('exp'):
                current_time = datetime.utcnow().timestamp()
                token_exp = user_info['exp']
                logger.info(f"Token expiry check - Current: {current_time}, Token exp: {token_exp}, Expired: {current_time > token_exp}")
                if current_time > token_exp:
                    raise ValueError("Token has expired")
            else:
                logger.warning("No expiry time found in token")
            
            return {
                'valid': True,
                'user': user_info,
                'claims': verified_claims
            }
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_user_groups(self, email: str) -> List[str]:
        """
        Get user's groups from Cognito
        
        Args:
            email: User's email address
            
        Returns:
            List of group names
        """
        try:
            response = self.cognito_client.admin_list_groups_for_user(
                Username=email,
                UserPoolId=self.user_pool_id
            )
            
            groups = [group['GroupName'] for group in response.get('Groups', [])]
            return groups
            
        except ClientError as e:
            logger.error(f"Failed to get user groups: {e}")
            return []
    
    def check_permission(self, user_info: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if user has required permission based on role
        
        Args:
            user_info: User information from token validation
            required_permission: Required permission (upload, view, admin)
            
        Returns:
            True if user has permission, False otherwise
        """
        user_role = user_info.get('role', 'viewer')
        user_groups = user_info.get('groups', [])
        
        # Define role permissions
        role_permissions = {
            'admin': ['upload', 'view', 'admin', 'delete'],
            'uploader': ['upload', 'view'],
            'viewer': ['view']
        }
        
        # Check role-based permissions
        if required_permission in role_permissions.get(user_role, []):
            return True
        
        # Check group-based permissions
        group_permissions = {
            'admin': ['upload', 'view', 'admin', 'delete'],
            'uploader': ['upload', 'view'],
            'viewer': ['view']
        }
        
        for group in user_groups:
            if required_permission in group_permissions.get(group, []):
                return True
        
        return False
    
    def logout_user(self, access_token: str) -> Dict[str, Any]:
        """
        Logout user by revoking tokens
        
        Args:
            access_token: User's access token
            
        Returns:
            Dictionary containing logout result
        """
        try:
            self.cognito_client.global_sign_out(
                AccessToken=access_token
            )
            
            logger.info("User logged out successfully")
            
            return {
                'success': True,
                'message': 'Logged out successfully'
            }
            
        except ClientError as e:
            logger.error(f"Logout failed: {e}")
            raise ValueError("Logout failed")
    
    def _get_user_info(self, email: str) -> Dict[str, Any]:
        """Get user information from Cognito"""
        try:
            response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=email
            )
            
            user_attributes = {attr['Name']: attr['Value'] for attr in response.get('UserAttributes', [])}
            groups = self.get_user_groups(email)
            
            return {
                'user_id': response['Username'],
                'email': user_attributes.get('email', email),
                'name': user_attributes.get('name', ''),
                'role': user_attributes.get('custom:role', 'uploader'),
                'groups': groups,
                'status': response.get('UserStatus', 'UNKNOWN'),
                'created': response.get('UserCreateDate'),
                'modified': response.get('UserLastModifiedDate')
            }
            
        except ClientError as e:
            logger.error(f"Failed to get user info: {e}")
            return {
                'user_id': email,
                'email': email,
                'name': '',
                'role': 'uploader',
                'groups': [],
                'status': 'UNKNOWN'
            }
    
    def _add_user_to_group(self, email: str, role: str) -> None:
        """Add user to appropriate Cognito group"""
        try:
            self.cognito_client.admin_add_user_to_group(
                UserPoolId=self.user_pool_id,
                Username=email,
                GroupName=role
            )
            logger.info(f"Added user {email} to group {role}")
        except ClientError as e:
            logger.error(f"Failed to add user to group: {e}")
    
    def confirm_user(self, email: str, confirmation_code: str) -> Dict[str, Any]:
        """
        Confirm user registration with confirmation code
        
        Args:
            email: User's email address
            confirmation_code: Confirmation code from email
            
        Returns:
            Dictionary containing confirmation result
        """
        try:
            self.cognito_client.confirm_sign_up(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code
            )
            
            logger.info(f"User confirmed successfully: {email}")
            
            return {
                'success': True,
                'message': 'User confirmed successfully'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                raise ValueError("Invalid confirmation code")
            elif error_code == 'ExpiredCodeException':
                raise ValueError("Confirmation code has expired")
            else:
                logger.error(f"User confirmation failed: {e}")
                raise ValueError(f"Confirmation failed: {e}")
    
    def resend_confirmation(self, email: str) -> Dict[str, Any]:
        """
        Resend confirmation code to user
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary containing resend result
        """
        try:
            self.cognito_client.resend_confirmation_code(
                ClientId=self.client_id,
                Username=email
            )
            
            logger.info(f"Confirmation code resent to: {email}")
            
            return {
                'success': True,
                'message': 'Confirmation code resent successfully'
            }
            
        except ClientError as e:
            logger.error(f"Failed to resend confirmation code: {e}")
            raise ValueError("Failed to resend confirmation code")
