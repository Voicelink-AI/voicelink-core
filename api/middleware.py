"""
Custom middleware for VoiceLink Core API
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from config.implementation_status import get_implementation_status

class ImplementationStatusMiddleware(BaseHTTPMiddleware):
    """Add implementation status to response headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add implementation status header
        status = get_implementation_status()
        implemented_features = [k for k, v in status.items() if v.get("implemented", False)]
        
        response.headers["X-VoiceLink-Implemented-Features"] = ",".join(implemented_features)
        response.headers["X-VoiceLink-Status"] = "development"
        
        return response
