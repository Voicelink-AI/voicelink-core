"""
API Utilities for VoiceLink

Shared utility functions for the FastAPI application.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException, Request
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def create_response(
    data: Any = None,
    message: str = "Success",
    status: str = "success",
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create standardized API response
    
    Args:
        data: Response data
        message: Response message
        status: Response status (success/error)
        metadata: Additional metadata
        
    Returns:
        Standardized response dictionary
    """
    response = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_error_response(
    message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create standardized error response
    """
    response = {
        "status": "error",
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


async def log_request(request: Request):
    """Log incoming API requests"""
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    
    logger.info(f"{method} {url} from {client_ip}")


def validate_audio_file(file_path: str) -> bool:
    """Validate audio file format and size"""
    if not file_path:
        return False
    
    supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg']
    file_ext = Path(file_path).suffix.lower()
    return file_ext in supported_formats


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for storage"""
    import re
    # Remove unsafe characters
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return safe_filename


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
