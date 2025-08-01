"""
Simplified API routes for VoiceLink Core - No external service dependencies
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from enum import Enum
import uuid
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage only
meetings_storage: Dict[str, Dict[str, Any]] = {}
uploaded_files: Dict[str, Dict[str, Any]] = {}

# Hardcoded storage path
AUDIO_STORAGE_PATH = "./audio_storage"

# Response Models
class ProcessMeetingResponse(BaseModel):
    meeting_id: Optional[str]
    transcript: dict
    speakers: list
    technical_terms: list
    error: Optional[str] = None

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Utility functions
def normalize_transcript(val) -> dict:
    """Ensure transcript is always a dict for ProcessMeetingResponse."""
    try:
        if isinstance(val, dict):
            return val
        if isinstance(val, str):
            if val.strip() == "":
                return {}
            return {"full_text": [val]}
        if val is None:
            return {}
        return {"full_text": [str(val)]}
    except Exception:
        return {"full_text": ["Error processing transcript"]}

def save_audio_file_simple(file_bytes: bytes, filename: str, file_id: str) -> str:
    """Simple audio file save function"""
    try:
        storage_path = Path(AUDIO_STORAGE_PATH)
        storage_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(filename).suffix
        stored_filename = f"{timestamp}_{file_id}{file_ext}"
        
        file_path = storage_path / stored_filename
        
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        logger.info(f"Audio file saved: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logger.error(f"Failed to save audio file: {e}")
        return f"{AUDIO_STORAGE_PATH}/fallback_{file_id}.wav"

# Endpoints
@router.post("/process-meeting", response_model=ProcessMeetingResponse, tags=["Audio Processing"])
async def process_meeting_simple(file: UploadFile = File(...), format: str = "wav"):
    """
    Simple process meeting endpoint with no external dependencies
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".wav", ".mp3", ".m4a", ".flac", ".ogg"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_ext}"
            )
        
        # Read file
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        logger.info(f"Processing audio file: {file.filename} ({len(file_bytes)} bytes)")
        
        # Generate unique meeting ID
        meeting_id = f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Save file
        file_path = save_audio_file_simple(file_bytes, file.filename, meeting_id)
        
        # Save to in-memory storage
        uploaded_files[meeting_id] = {
            "file_id": meeting_id,
            "filename": file.filename,
            "content_type": getattr(file, 'content_type', 'audio/wav'),
            "size": len(file_bytes),
            "uploaded_at": datetime.now().isoformat(),
            "status": "processed",
            "file_path": file_path
        }
        
        # Generate mock processing result
        mock_result = {
            "transcript": {
                "full_text": f"Simple mock transcript for {file.filename}: File uploaded and processed successfully using the simplified endpoint.",
                "segments": [
                    {
                        "speaker_id": "Speaker_1",
                        "text": f"Simple mock transcript for {file.filename}: File uploaded and processed successfully.",
                        "start_time": 0.0,
                        "end_time": 10.0,
                        "confidence": 0.85
                    }
                ],
                "total_segments": 1
            },
            "speakers": [
                {
                    "speaker_id": "Speaker_1",
                    "segments": [
                        {
                            "text": "Simple mock transcript showing successful file upload",
                            "timestamp": "00:00:00",
                            "confidence": 0.85,
                            "duration": 10.0
                        }
                    ],
                    "total_speaking_time": 10.0
                }
            ],
            "technical_terms": ["simple", "mock", "transcript", "file", "upload"],
        }
        
        transcript_dict = normalize_transcript(mock_result["transcript"])
        
        logger.info(f"Simple processing completed for: {meeting_id}")
        
        return ProcessMeetingResponse(
            meeting_id=meeting_id,
            transcript=transcript_dict,
            speakers=mock_result["speakers"],
            technical_terms=mock_result["technical_terms"],
            error=None  # No error in simple mode
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simple process_meeting failed: {e}")
        logger.exception("Full traceback:")
        return ProcessMeetingResponse(
            meeting_id=None,
            transcript=normalize_transcript({}),
            speakers=[],
            technical_terms=[],
            error=f"Simple processing error: {str(e)}"
        )

@router.get("/health-simple", tags=["System"])
async def health_check_simple():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "VoiceLink Simple API is running",
        "mode": "simple",
        "files_processed": len(uploaded_files)
    }

@router.get("/debug-simple", tags=["System"])
async def debug_simple():
    """Simple debug endpoint"""
    return {
        "uploaded_files_count": len(uploaded_files),
        "meetings_count": len(meetings_storage),
        "storage_path": AUDIO_STORAGE_PATH,
        "message": "Simple debug info"
    }
