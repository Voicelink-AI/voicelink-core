"""
VoiceLink Core API Server
"""
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use the FIXED routes instead of the problematic ones
from api.routes_fixed import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceLink Core API",
    description="Comprehensive meeting transcription and AI analysis platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VoiceLink Core API (Fixed Version)",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_base": "/api/v1"
    }

# Add root-level health endpoint to avoid 404s
@app.get("/health", tags=["Root"])
async def root_health():
    """Root health check endpoint"""
    return {
        "status": "healthy",
        "message": "VoiceLink API is running",
        "api_health": "/api/v1/health"
    }

if __name__ == "__main__":
    logger.info("Starting VoiceLink Core API server (Fixed Version)...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
