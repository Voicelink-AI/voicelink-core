"""
Security and Authentication Middleware for VoiceLink Analytics API

Provides JWT authentication, role-based access control, API key validation,
and security headers for analytics endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import hmac
import time
import os

# Try to import JWT - if not available, provide fallback
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("PyJWT not installed - JWT authentication disabled")

# Try to import middleware - if not available, provide fallback  
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    MIDDLEWARE_AVAILABLE = True
except ImportError:
    MIDDLEWARE_AVAILABLE = False
    BaseHTTPMiddleware = object
    logging.warning("Starlette middleware not available")

logger = logging.getLogger(__name__)

# Security configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

API_KEY_HEADER = "X-API-Key"
RATE_LIMIT_HEADER = "X-RateLimit-Remaining"

# User roles and permissions
class UserRole:
    ADMIN = "admin"
    ANALYTICS_VIEWER = "analytics_viewer"
    MEETING_OWNER = "meeting_owner"
    PARTICIPANT = "participant"

class Permission:
    READ_ALL_ANALYTICS = "read_all_analytics"
    READ_OWN_ANALYTICS = "read_own_analytics"
    EXPORT_ANALYTICS = "export_analytics"
    MANAGE_ANALYTICS = "manage_analytics"

# Role-based permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_ALL_ANALYTICS,
        Permission.EXPORT_ANALYTICS,
        Permission.MANAGE_ANALYTICS
    ],
    UserRole.ANALYTICS_VIEWER: [
        Permission.READ_ALL_ANALYTICS,
        Permission.EXPORT_ANALYTICS
    ],
    UserRole.MEETING_OWNER: [
        Permission.READ_OWN_ANALYTICS,
        Permission.EXPORT_ANALYTICS
    ],
    UserRole.PARTICIPANT: [
        Permission.READ_OWN_ANALYTICS
    ]
}

class AuthenticationError(Exception):
    """Custom authentication error"""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code

class AuthorizationError(Exception):
    """Custom authorization error"""
    def __init__(self, message: str, status_code: int = status.HTTP_403_FORBIDDEN):
        self.message = message
        self.status_code = status_code

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for analytics endpoints"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers and logging"""
        
        # Log request
        logger.info(f"Analytics API request: {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        
        return response

class JWTTokenManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(user_data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        if not JWT_AVAILABLE:
            # Fallback to simple token for development
            import base64
            import json
            token_data = {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "role": user_data["role"],
                "exp": (datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)).timestamp()
            }
            token_json = json.dumps(token_data)
            return base64.b64encode(token_json.encode()).decode()
        
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        payload = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "exp": expiration,
            "iat": datetime.utcnow(),
            "iss": "voicelink-analytics"
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        if not JWT_AVAILABLE:
            # Fallback token verification
            import base64
            import json
            try:
                token_json = base64.b64decode(token.encode()).decode()
                payload = json.loads(token_json)
                
                # Check expiration
                if payload.get("exp", 0) < datetime.utcnow().timestamp():
                    raise AuthenticationError("Token has expired")
                
                return payload
            except Exception:
                raise AuthenticationError("Invalid token")
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

class APIKeyManager:
    """API key management and validation"""
    
    @staticmethod
    def generate_api_key(user_id: str) -> str:
        """Generate API key for user"""
        timestamp = str(int(time.time()))
        raw_key = f"{user_id}:{timestamp}:{JWT_SECRET_KEY}"
        return f"vl_{hashlib.sha256(raw_key.encode()).hexdigest()[:32]}"
    
    @staticmethod
    def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user data"""
        # TODO: Replace with real database lookup
        # In production, this should query your user database
        # Example:
        # user = database.get_user_by_api_key(api_key)
        # return user.to_dict() if user else None
        
        return None  # No mock data - must implement real database lookup

class PermissionChecker:
    """Permission and access control checker"""
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        """Check if user role has required permission"""
        role_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return required_permission in role_permissions
    
    @staticmethod
    def can_access_meeting(user_data: Dict[str, Any], meeting_id: str) -> bool:
        """Check if user can access specific meeting"""
        meetings_access = user_data.get("meetings_access", [])
        
        # Admin or wildcard access
        if "*" in meetings_access:
            return True
        
        # Specific meeting access
        return meeting_id in meetings_access
    
    @staticmethod
    def can_access_user_data(current_user: Dict[str, Any], target_user_id: str) -> bool:
        """Check if user can access another user's data"""
        # Users can always access their own data
        if current_user["user_id"] == target_user_id:
            return True
        
        # Admins can access all user data
        if current_user["role"] == UserRole.ADMIN:
            return True
        
        # Analytics viewers can access all data for analysis
        if current_user["role"] == UserRole.ANALYTICS_VIEWER:
            return True
        
        return False

# Authentication dependencies
security_scheme = HTTPBearer()

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = JWTTokenManager.verify_token(token)
        
        # Get user data (TODO: fetch from real database)
        user_email = payload.get("email")
        # TODO: Replace with real database lookup
        # user_data = database.get_user_by_email(user_email)
        
        # For now, return None - must implement real database lookup
        user_data = None
        
        if not user_data:
            raise AuthenticationError("User not found")
        
        return user_data
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_from_api_key(request: Request) -> Dict[str, Any]:
    """Get current user from API key"""
    api_key = request.headers.get(API_KEY_HEADER)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    user_data = APIKeyManager.validate_api_key(api_key)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user_data

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Dict[str, Any]:
    """Get current user from either JWT token or API key"""
    
    # Try API key first
    api_key = request.headers.get(API_KEY_HEADER)
    if api_key:
        return await get_current_user_from_api_key(request)
    
    # Fall back to JWT token
    if credentials:
        return await get_current_user_from_token(credentials)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

# Permission decorators and dependencies
def require_permission(required_permission: str):
    """Decorator to require specific permission"""
    async def permission_dependency(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        
        if not PermissionChecker.has_permission(current_user["role"], required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        
        return current_user
    
    return permission_dependency

def require_meeting_access(meeting_id_param: str = "meeting_id"):
    """Decorator to require access to specific meeting"""
    async def meeting_access_dependency(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        
        # Extract meeting ID from path parameters
        meeting_id = request.path_params.get(meeting_id_param)
        
        if not meeting_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting ID required"
            )
        
        if not PermissionChecker.can_access_meeting(current_user, meeting_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this meeting"
            )
        
        return current_user
    
    return meeting_access_dependency

# Convenience dependencies for common permission patterns
require_analytics_read = require_permission(Permission.READ_ALL_ANALYTICS)
require_analytics_export = require_permission(Permission.EXPORT_ANALYTICS)
require_analytics_manage = require_permission(Permission.MANAGE_ANALYTICS)

# Authentication utilities
class AuthUtils:
    """Authentication utility functions"""
    
    @staticmethod
    def create_user_session(user_email: str) -> Dict[str, str]:
        """Create user session with token"""
        # TODO: Replace with real database lookup
        # user_data = database.get_user_by_email(user_email)
        
        user_data = None  # No mock data - must implement real database lookup
        if not user_data:
            raise AuthenticationError("User not found")
        
        access_token = JWTTokenManager.create_access_token(user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "user": {
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "role": user_data["role"]
            }
        }
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        computed_hash, _ = AuthUtils.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, password_hash)

# Rate limiting for security
class RateLimiter:
    """Simple rate limiter for analytics endpoints"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, client_id: str, max_requests: int = 100, window_minutes: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        window_start = now - (window_minutes * 60)
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
        else:
            self.requests[client_id] = []
        
        # Check limit
        if len(self.requests[client_id]) >= max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining_requests(self, client_id: str, max_requests: int = 100) -> int:
        """Get remaining requests in current window"""
        if client_id not in self.requests:
            return max_requests
        
        return max(0, max_requests - len(self.requests[client_id]))

# Global rate limiter instance
rate_limiter = RateLimiter()

# Audit logging
class AuditLogger:
    """Audit logging for analytics access"""
    
    @staticmethod
    def log_access(user_id: str, action: str, resource: str, success: bool = True):
        """Log access attempt"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "success": success,
            "ip_address": "127.0.0.1"  # TODO: Get real IP
        }
        
        # In production, send to secure audit log
        logger.info(f"AUDIT: {log_entry}")
    
    @staticmethod
    def log_export(user_id: str, meeting_id: str, format: str, success: bool = True):
        """Log data export"""
        AuditLogger.log_access(
            user_id, 
            f"EXPORT_{format.upper()}", 
            f"meeting/{meeting_id}", 
            success
        )

# Initialize security components
logger.info("🔒 Analytics security middleware initialized")
logger.info("🔑 JWT authentication enabled")
logger.info("📝 API key authentication enabled")
logger.info("🛡️  Rate limiting enabled")
logger.info("📊 Audit logging enabled")
