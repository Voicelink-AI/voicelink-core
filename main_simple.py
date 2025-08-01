"""
Simple VoiceLink Core API Server for testing
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the simple routes
from api.routes_simple import router as simple_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceLink Core API (Simple)",
    description="Simplified version for testing",
    version="1.0.0-simple"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include simple routes
app.include_router(simple_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "VoiceLink Core API (Simple Mode)",
        "version": "1.0.0-simple",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting VoiceLink Core API server (Simple Mode)...")
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port
