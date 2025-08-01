"""
Enhanced VoiceLink Core API Server with Real Processing
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use the enhanced routes
from api.routes_enhanced import router as enhanced_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceLink Core API (Enhanced)",
    description="Enhanced version with real audio processing capabilities",
    version="1.0.0-enhanced"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(enhanced_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VoiceLink Core API (Enhanced Version)",
        "version": "1.0.0-enhanced",
        "status": "running",
        "docs": "/docs",
        "features": [
            "Real audio processing",
            "Enhanced transcription",
            "Speaker diarization", 
            "Technical term extraction",
            "LLM integration ready"
        ]
    }

# Add root-level health endpoint to avoid 404s
@app.get("/health", tags=["Root"])
async def root_health():
    """Root health check endpoint"""
    return {
        "status": "healthy",
        "message": "VoiceLink Enhanced API is running",
        "api_health": "/api/v1/health-enhanced",
        "version": "1.0.0-enhanced"
    }

if __name__ == "__main__":
    logger.info("Starting VoiceLink Core API server (Enhanced Version)...")
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
