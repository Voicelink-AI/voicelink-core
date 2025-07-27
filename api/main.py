from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import logging
from pathlib import Path
import sys
import os
import tempfile
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from api.config import Config

# Import routers
from api.routers import health

# Import the new meetings router
try:
    from api.routers import meetings_new as meetings
    MEETINGS_ROUTER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"New meetings router not available: {e}")
    # Fallback to old meetings router
    try:
        from api.routers import meetings
        MEETINGS_ROUTER_AVAILABLE = True
    except ImportError as e2:
        logging.warning(f"Meetings router not available: {e2}")
        MEETINGS_ROUTER_AVAILABLE = False

# Try to import orchestrator from new location
try:
    from core.orchestrator import VoiceLinkOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Orchestrator not available: {e}")
    ORCHESTRATOR_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VoiceLink API",
    description="AI-powered documentation pipeline for voice recordings",
    version=Config.APP_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)

if MEETINGS_ROUTER_AVAILABLE:
    app.include_router(meetings.router)
    logger.info("✅ Meetings router loaded successfully")
else:
    logger.warning("⚠️  Meetings router not available - some endpoints will not work")

# Include analytics router (new comprehensive endpoints)
try:
    from api.analytics_endpoints import router as analytics_endpoints_router
    app.include_router(analytics_endpoints_router)
    logger.info("✅ Analytics endpoints router loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  Analytics endpoints router not available: {e}")

# Include legacy analytics router
try:
    from analytics.api import router as analytics_router
    app.include_router(analytics_router)
    logger.info("✅ Analytics router loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️  Analytics router not available: {e}")

# Initialize orchestrator if available
orchestrator = None
if ORCHESTRATOR_AVAILABLE:
    try:
        orchestrator_config = Config.get_llm_config()
        orchestrator_config.update({
            "whisper_model": Config.WHISPER_MODEL,
            "vosk_model_path": Config.VOSK_MODEL_PATH,
            "huggingface_token": Config.HUGGINGFACE_TOKEN
        })
        orchestrator = VoiceLinkOrchestrator(orchestrator_config)
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        orchestrator = None

@app.get("/")
async def root():
    return {
        "message": "Voicelink AI-Powered Documentation Pipeline",
        "version": Config.APP_VERSION,
        "build": Config.BUILD_ID,
        "status": "operational",
        "capabilities": {
            "audio_processing": orchestrator is not None,
            "speaker_diarization": True,
            "speech_to_text": True,
            "llm_processing": True,
            "code_context": True,
            "meetings_api": MEETINGS_ROUTER_AVAILABLE
        },
        "endpoints": {
            "health": "/health",
            "process_audio": "/process-audio/",
            "upload_audio": "/upload-audio/",
            "version": "/version",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    health_status = await health.health_check()
    
    # Add orchestrator health
    if orchestrator:
        models_status = {
            "orchestrator": True,
            "diarization": orchestrator.diarization_pipeline is not None,
            "whisper": orchestrator.whisper_model is not None,
            "vosk": orchestrator.vosk_model is not None
        }
        health_status["models"] = models_status
    else:
        health_status["models"] = {"orchestrator": False}
    
    return health_status

@app.get("/version")
async def version_info():
    return {
        "version": Config.APP_VERSION,
        "build": Config.BUILD_ID,
        "docs": "/docs",
        "orchestrator_available": orchestrator is not None
    }

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for processing"""
    if not file.filename.lower().endswith(tuple(Config.SUPPORTED_AUDIO_FORMATS)):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Supported formats: {Config.SUPPORTED_AUDIO_FORMATS}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > Config.MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {Config.MAX_AUDIO_SIZE_MB}MB"
        )
    
    # Save file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(file_content)
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "size_mb": round(file_size_mb, 2),
        "temp_path": str(temp_path),
        "status": "ready_for_processing"
    }

@app.post("/process-audio/")
async def process_audio_endpoint(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Process audio file through the complete AI pipeline"""
    if not orchestrator:
        raise HTTPException(
            status_code=503,
            detail="Audio processing orchestrator not available. Check configuration and dependencies."
        )
    
    if not file.filename.lower().endswith(tuple(Config.SUPPORTED_AUDIO_FORMATS)):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Supported formats: {Config.SUPPORTED_AUDIO_FORMATS}"
        )
    
    # Check file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    if file_size_mb > Config.MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {Config.MAX_AUDIO_SIZE_MB}MB"
        )
    
    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(file_content)
    
    try:
        logger.info(f"Processing audio file: {file.filename}")
        
        # Process through pipeline
        result = await orchestrator.process_audio_session(
            audio_file=Path(str(temp_path)),
            session_id=None,
            participants=None,
            metadata={"uploaded_filename": file.filename, "file_size_mb": file_size_mb}
        )
        
        # Convert result to dict for JSON response
        result_dict = {
            "session_id": result.session_id,
            "status": "success",
            "processing_timestamp": result.start_time.isoformat(),
            "participants": result.participants,
            "metadata": result.metadata,
            "vad_segments_count": len(result.vad_segments),
            "transcription_segments_count": len(result.transcriptions),
            "llm_outputs": result.llm_outputs,
            "file_info": {
                "filename": file.filename,
                "size_mb": round(file_size_mb, 2),
                "format": Path(file.filename).suffix
            }
        }
        
        logger.info(f"Successfully processed: {file.filename}")
        return JSONResponse(content=result_dict)
        
    except Exception as e:
        logger.error(f"Processing failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Clean up temp file in background
        if background_tasks and temp_path.exists():
            background_tasks.add_task(cleanup_temp_file, temp_path)

async def cleanup_temp_file(file_path: Path):
    """Clean up temporary file"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temp file {file_path}: {e}")

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities and model status"""
    if not orchestrator:
        return {
            "orchestrator": False,
            "message": "Orchestrator not available"
        }
    
    return {
        "orchestrator": True,
        "audio_processing": {
            "cpp_engine_available": hasattr(orchestrator, 'audio_engine_py') and orchestrator.audio_engine_py is not None,
            "python_fallback": True
        },
        "speaker_diarization": {
            "pyannote_available": orchestrator.diarization_pipeline is not None,
            "model": "pyannote/speaker-diarization-3.1" if orchestrator.diarization_pipeline else None
        },
        "speech_to_text": {
            "whisper_available": orchestrator.whisper_model is not None,
            "whisper_model": Config.WHISPER_MODEL if orchestrator.whisper_model else None,
            "vosk_available": orchestrator.vosk_model is not None,
            "vosk_model_path": Config.VOSK_MODEL_PATH if orchestrator.vosk_model else None
        },
        "llm_processing": {
            "providers_available": list(orchestrator.llm_engine.providers.keys()) if hasattr(orchestrator, 'llm_engine') else []
        },
        "supported_formats": Config.SUPPORTED_AUDIO_FORMATS,
        "max_file_size_mb": Config.MAX_AUDIO_SIZE_MB
    }

@app.post("/process-meeting")
async def process_meeting(audio_file: UploadFile = File(...)) -> Dict[str, Any]:
    """Process a meeting audio file"""
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        content = await audio_file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process with Voicelink
        from llm_engine.enhanced_pipeline_with_context import process_audio_with_context
        from llm_engine.modules.doc_generator import generate_meeting_documentation
        from llm_engine.modules.voice_qa import add_meeting_to_qa
        from blockchain.simple_provenance import create_meeting_provenance
        
        # Process audio
        voicelink_results = process_audio_with_context(tmp_file_path)
        
        if voicelink_results.get('status') != 'success':
            return {"error": "Audio processing failed"}
        
        # Generate documentation
        documentation = generate_meeting_documentation(voicelink_results)
        
        # Add to Q&A knowledge base
        add_meeting_to_qa(voicelink_results)
        
        # Create provenance
        provenance = create_meeting_provenance(voicelink_results, documentation)
        
        return {
            "status": "success",
            "voicelink_analysis": voicelink_results,
            "documentation": documentation,
            "provenance": provenance
        }
        
    finally:
        # Cleanup
        os.unlink(tmp_file_path)

@app.post("/ask-question")
async def ask_question(question_data: Dict[str, str]) -> Dict[str, Any]:
    """Ask a question about processed meetings"""
    from llm_engine.modules.voice_qa import ask_voice_question
    
    question = question_data.get("question", "")
    if not question:
        return {"error": "No question provided"}
    
    answer = ask_voice_question(question)
    return answer
