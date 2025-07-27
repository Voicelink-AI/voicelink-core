"""
Health check router
"""
from fastapi import APIRouter, HTTPException
from fastapi import status
from typing import Dict, Any
from ..config import Config
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Simple health check endpoint for frontend polling"""
    return {
        "status": "healthy",
        "service": "voicelink-core",
        "version": "1.0.0",
        "timestamp": "2025-01-27T12:00:00Z"
    }

@router.get("/status")
async def detailed_status() -> Dict[str, Any]:
    """Detailed status check with dependency information"""
    try:
        # Check basic service health
        service_health = {
            "status": "healthy",
            "service": "voicelink-core",
            "version": Config.APP_VERSION if hasattr(Config, 'APP_VERSION') else "1.0.0"
        }
        
        # Check optional dependencies
        dependencies = {}
        
        # Check ElevenLabs API if configured
        if hasattr(Config, 'ELEVENLABS_API_KEY') and Config.ELEVENLABS_API_KEY:
            try:
                elevenlabs_ok = await is_elevenlabs_alive()
                dependencies["elevenlabs_api"] = elevenlabs_ok
            except Exception as e:
                logger.warning(f"ElevenLabs check failed: {e}")
                dependencies["elevenlabs_api"] = False
        
        # Check audio processing capabilities
        try:
            from audio_engine.python.audio_bridge import AUDIO_ENGINE_AVAILABLE
            dependencies["audio_engine"] = AUDIO_ENGINE_AVAILABLE
        except Exception:
            dependencies["audio_engine"] = False
            
        # Check LLM capabilities
        try:
            from llm_engine.enhanced_pipeline_with_context import code_aware_pipeline
            dependencies["llm_pipeline"] = True
        except Exception:
            dependencies["llm_pipeline"] = False
        
        return {
            **service_health,
            "dependencies": dependencies
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": f"Service health check failed: {e}"
            }
        )

async def is_elevenlabs_alive() -> bool:
    """Check if ElevenLabs API is accessible"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.elevenlabs.io/v1/models",
                headers={"xi-api-key": Config.ELEVENLABS_API_KEY},
                timeout=5.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"ElevenLabs API check failed: {e}")
        return False