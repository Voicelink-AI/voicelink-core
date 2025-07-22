from fastapi import FastAPI
from api.config import Config
from .routers import health

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Voicelink API",
        "endpoints": {
            "health": "/health",
            "version": "/version",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return await health.health_check()

@app.get("/version")
async def version_info():
    return {
        "version": Config.APP_VERSION,
        "build": Config.BUILD_ID,
        "docs": "/docs"
    }
    