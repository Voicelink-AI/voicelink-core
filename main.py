"""
Main FastAPI application entry point for VoiceLink
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.meetings_new import router as meetings_router
from api.routers.health import router as health_router
from api.middleware import ImplementationStatusMiddleware

app = FastAPI(
    title="VoiceLink Core API",
    description="""
    **VoiceLink Core API** - Real-time voice processing and LLM integration
    
    ## Implementation Status
    🚧 **This API is in development mode** 🚧
    
    Most endpoints will return 501 (Not Implemented) until core modules are configured.
    
    ## Setup Required
    1. Deploy audio engine: `python scripts/deploy_audio_engine.py`
    2. Configure LLM providers (OpenAI, Anthropic, etc.)
    3. Set up database for persistence
    4. Configure Web3 provider for blockchain features
    
    ## Currently Working
    * Basic API structure and documentation
    * Health checks and system status
    * File upload (without processing)
    
    Check the implementation status in response headers: `X-VoiceLink-Implemented-Features`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add implementation status middleware
app.add_middleware(ImplementationStatusMiddleware)

# Include API routes
app.include_router(meetings_router)
app.include_router(health_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "VoiceLink Core API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "api_base": "/api"
    }

@app.get("/health", tags=["Root"])
async def health_check():
    return {"status": "healthy", "service": "voicelink-core"}

# Add a simple test endpoint at root level
@app.get("/ping", tags=["Root"])
async def ping():
    return {"message": "pong"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
