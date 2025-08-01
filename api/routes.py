"""
API routes for VoiceLink Core
"""
from fastapi import APIRouter, HTTPException, WebSocket, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
from enum import Enum
import uuid
from pathlib import Path

# Configure logging first
logging.basicConfig(level=logging.INFO)

router = APIRouter()

# In-memory storage for development (replace with database later)
meetings_storage: Dict[str, Dict[str, Any]] = {}
uploaded_files: Dict[str, Dict[str, Any]] = {}

# Initialize ALL variables as None at module level - CRITICAL
audio_service = None
meeting_service = None
SERVICES_AVAILABLE = False
AUDIO_STORAGE_PATH = "./audio_storage"

# Stub functions for audio engine
def transcribe_audio_file_stub(file_bytes: bytes, format: str = "wav"):
    return {"transcript": "", "speakers": [], "technical_terms": []}

def is_available_stub():
    return False

# Set initial values
transcribe_audio_file = transcribe_audio_file_stub
is_available = is_available_stub

# Helper function to calculate analytics from real data
def calculate_analytics_from_meetings():
    """Calculate real analytics from stored meetings"""
    try:
        if not meetings_storage:
            return {
                "total_meetings": 0,
                "total_participants": 0,
                "total_minutes_recorded": 0.0,
                "avg_meeting_duration": 0.0,
                "active_meetings": 0,
                "completed_meetings": 0,
                "scheduled_meetings": 0
            }
        
        meetings = list(meetings_storage.values())
        total_meetings = len(meetings)
        
        # Count participants (unique emails across all meetings)
        all_participants = set()
        for meeting in meetings:
            for participant in meeting.get("participants", []):
                if isinstance(participant, dict) and "email" in participant:
                    all_participants.add(participant["email"])
                elif isinstance(participant, str):
                    all_participants.add(participant)
        
        # Count by status
        active_meetings = completed_meetings = scheduled_meetings = 0
        try:
            active_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.ACTIVE])
            completed_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.COMPLETED])
            scheduled_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.SCHEDULED])
        except:
            pass
        
        # Calculate duration for completed meetings
        total_duration_minutes = 0.0
        meetings_with_duration = 0
        
        for meeting in meetings:
            if meeting.get("start_time") and meeting.get("end_time"):
                try:
                    start = datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(meeting["end_time"].replace('Z', '+00:00'))
                    duration = (end - start).total_seconds() / 60
                    total_duration_minutes += duration
                    meetings_with_duration += 1
                except:
                    pass
        
        avg_duration = total_duration_minutes / meetings_with_duration if meetings_with_duration > 0 else 0.0
        
        return {
            "total_meetings": total_meetings,
            "total_participants": len(all_participants),
            "total_minutes_recorded": total_duration_minutes,
            "avg_meeting_duration": avg_duration,
            "active_meetings": active_meetings,
            "completed_meetings": completed_meetings,
            "scheduled_meetings": scheduled_meetings
        }
    except Exception as e:
        logging.error(f"Error calculating analytics: {e}")
        return {
            "total_meetings": 0,
            "total_participants": 0,
            "total_minutes_recorded": 0.0,
            "avg_meeting_duration": 0.0,
            "active_meetings": 0,
            "completed_meetings": 0,
            "scheduled_meetings": 0
        }

# Request/Response Models
class AudioProcessRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    format: str = "wav"
    language: Optional[str] = "auto"

class AudioProcessResponse(BaseModel):
    success: bool
    transcription: str = ""
    llm_response: str = ""
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    error: str = ""

class LLMRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 150
    temperature: float = 0.7

class LLMResponse(BaseModel):
    response: str
    model_used: str
    tokens_used: int
    cost_estimate: float

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[dict]
    created_at: str
    updated_at: str

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MeetingCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    scheduled_start: Optional[str] = None
    duration_minutes: int = 60
    participants: List[str] = []
    recording_enabled: bool = True
    transcription_enabled: bool = True
    ai_summary_enabled: bool = True
    audio_file_id: Optional[str] = None

class MeetingResponse(BaseModel):
    meeting_id: str
    title: str
    status: MeetingStatus
    participants: List[dict]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    ai_summary: Optional[str] = None
    action_items: List[str] = []
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class BlockchainTransaction(BaseModel):
    transaction_hash: str
    wallet_address: str
    amount: float
    currency: str = "MATIC"
    gas_fee: float
    status: str
    timestamp: datetime

class AnalyticsResponse(BaseModel):
    total_meetings: int
    total_participants: int
    total_minutes_recorded: float
    avg_meeting_duration: float
    top_speakers: List[dict]
    sentiment_analysis: dict
    word_cloud_data: List[dict]

class ProcessMeetingResponse(BaseModel):
    meeting_id: Optional[str]
    transcript: dict
    speakers: list
    technical_terms: list
    error: Optional[str] = None

# Utility function to normalize transcript
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

def save_mock_audio_file(file_bytes: bytes, filename: str, file_id: str) -> str:
    """Fallback function to save audio file when services are not available"""
    try:
        # Create a simple storage directory
        global AUDIO_STORAGE_PATH
        storage_path = Path(AUDIO_STORAGE_PATH)
        storage_path.mkdir(exist_ok=True)
        
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(filename).suffix
        stored_filename = f"{timestamp}_{file_id}{file_ext}"
        
        file_path = storage_path / stored_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        logging.info(f"Mock audio file saved: {file_path}")
        return str(file_path)
        
    except Exception as e:
        logging.error(f"Failed to save mock audio file: {e}")
        return f"{AUDIO_STORAGE_PATH}/mock_{file_id}.wav"

# NOW import and initialize services after all variables are defined
def init_services():
    """Initialize services - called after all variables are defined"""
    global audio_service, meeting_service, SERVICES_AVAILABLE, AUDIO_STORAGE_PATH
    global transcribe_audio_file, is_available
    
    try:
        # Try to import audio engine
        try:
            from audio_engine.engine import transcribe_audio_file as taf, is_available as ia
            transcribe_audio_file = taf
            is_available = ia
            logging.info("Audio engine imported successfully")
        except ImportError as e:
            logging.warning(f"Audio engine not available: {e}")
        
        # Try to import services
        try:
            from services.audio_service import AudioProcessingService
            from services.meeting_service import MeetingService
            from database.connection import create_tables
            from config.settings import AUDIO_STORAGE_PATH as configured_path, ensure_directories
            
            AUDIO_STORAGE_PATH = configured_path
            
            # Initialize services
            ensure_directories()
            audio_service = AudioProcessingService(AUDIO_STORAGE_PATH)
            meeting_service = MeetingService()
            create_tables()
            SERVICES_AVAILABLE = True
            logging.info("All services initialized successfully")
            
        except ImportError as e:
            logging.warning(f"Services not available: {e}")
            audio_service = None
            meeting_service = None
            SERVICES_AVAILABLE = False
            
    except Exception as e:
        logging.error(f"Service initialization failed: {e}")
        audio_service = None
        meeting_service = None
        SERVICES_AVAILABLE = False

# Initialize services after everything is defined
init_services()

# Audio Processing Endpoints
@router.post("/process-audio", response_model=AudioProcessResponse, tags=["Audio Processing"])
async def process_audio(request: AudioProcessRequest):
    """Process audio through the complete VoiceLink pipeline"""
    try:
        raise HTTPException(
            status_code=501, 
            detail="Audio processing not yet implemented. Please integrate the audio engine module."
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-meeting", response_model=ProcessMeetingResponse, tags=["Audio Processing"])
async def process_meeting(file: UploadFile = File(...), format: str = "wav"):
    """
    Process meeting audio using the VoiceLink audio engine.
    Returns transcript, speaker separation, and technical term detection.
    """
    logger = logging.getLogger("voicelink.process_meeting")
    
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
        
        # Get current service status - use module globals
        current_services_available = globals().get('SERVICES_AVAILABLE', False)
        current_audio_service = globals().get('audio_service', None)
        current_meeting_service = globals().get('meeting_service', None)
        
        # Check if we can use full services
        if (current_services_available and 
            current_audio_service is not None and 
            current_meeting_service is not None):
            
            try:
                logger.info("Using full service stack for processing")
                
                # Save audio file
                file_path = current_audio_service.save_audio_file(
                    file_bytes=file_bytes,
                    filename=file.filename,
                    file_id=meeting_id
                )
                
                # Create meeting record
                meeting = current_meeting_service.create_meeting(
                    meeting_id=meeting_id,
                    title=f"Meeting from {file.filename}",
                    audio_file_path=file_path,
                    audio_file_name=file.filename,
                    audio_file_size=len(file_bytes)
                )
                
                # Process audio
                processing_result = current_audio_service.process_audio_file(file_path, format)
                
                # Update meeting with results
                current_meeting_service.update_meeting_results(
                    meeting_id=meeting_id,
                    transcript=processing_result["transcript"],
                    speakers=processing_result["speakers"],
                    technical_terms=processing_result["technical_terms"],
                    audio_duration=processing_result["audio_metadata"].get("duration"),
                    status="completed"
                )
                
                # Format response
                transcript_dict = normalize_transcript(processing_result["transcript"])
                
                logger.info(f"Successfully processed meeting with full stack: {meeting_id}")
                
                return ProcessMeetingResponse(
                    meeting_id=meeting_id,
                    transcript=transcript_dict,
                    speakers=processing_result["speakers"],
                    technical_terms=processing_result["technical_terms"],
                    error=None
                )
                
            except Exception as processing_error:
                logger.error(f"Full stack processing failed for {meeting_id}: {processing_error}")
                logger.exception("Full error traceback:")
                
                # Try to update meeting with error if possible
                if current_meeting_service is not None:
                    try:
                        current_meeting_service.update_meeting_results(
                            meeting_id=meeting_id,
                            transcript={},
                            speakers=[],
                            technical_terms=[],
                            status="error",
                            processing_error=str(processing_error)
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update meeting with error: {e}")
                
                # Fall through to mock processing
                logger.info("Falling back to mock processing due to error")
        else:
            logger.info("Services not available - using mock processing")
        
        # MOCK PROCESSING PATH - no service dependencies
        logger.warning("Using mock processing - services not fully available")
        
        # Save file using fallback method
        try:
            file_path = save_mock_audio_file(file_bytes, file.filename, meeting_id)
        except Exception as e:
            logger.error(f"Mock file save failed: {e}")
            file_path = f"./audio_storage/mock_{meeting_id}.wav"
        
        # Save to in-memory storage as fallback
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
                "full_text": f"Mock transcript for {file.filename}: This is a sample transcription showing that the file was uploaded successfully. The audio processing system is running in fallback mode.",
                "segments": [
                    {
                        "speaker_id": "Speaker_1",
                        "text": f"Mock transcript for {file.filename}: This is a sample transcription showing that the file was uploaded successfully.",
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
                            "text": "Mock transcript showing successful file upload and processing",
                            "timestamp": "00:00:00",
                            "confidence": 0.85,
                            "duration": 10.0
                        }
                    ],
                    "total_speaking_time": 10.0
                }
            ],
            "technical_terms": ["mock", "transcript", "file", "upload", "processing", "audio"],
            "audio_metadata": {
                "duration": 10.0,
                "sample_rate": 16000,
                "channels": 1
            }
        }
        
        transcript_dict = normalize_transcript(mock_result["transcript"])
        
        logger.info(f"Mock processing completed for: {meeting_id}")
        
        return ProcessMeetingResponse(
            meeting_id=meeting_id,
            transcript=transcript_dict,
            speakers=mock_result["speakers"],
            technical_terms=mock_result["technical_terms"],
            error="Running in fallback mode - full services not available"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"process_meeting failed with unexpected error: {e}")
        logger.exception("Full traceback:")
        return ProcessMeetingResponse(
            meeting_id=None,
            transcript=normalize_transcript({}),
            speakers=[],
            technical_terms=[],
            error=f"Unexpected error: {str(e)}"
        )

# Continue with other endpoints... (rest remain the same)
@router.post("/upload-audio", tags=["Audio Processing"])
async def upload_audio_file(file: UploadFile = File(...)):
    """Upload audio file for processing"""
    logger = logging.getLogger(__name__)
    
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Read file
        file_bytes = await file.read()
        
        # Get current service status
        current_services_available = globals().get('SERVICES_AVAILABLE', False)
        current_audio_service = globals().get('audio_service', None)
        current_meeting_service = globals().get('meeting_service', None)
        
        if (current_services_available and 
            current_audio_service is not None and 
            current_meeting_service is not None):
            
            logger.info("Using full service stack for file upload")
            # Save audio file using service
            file_path = current_audio_service.save_audio_file(
                file_bytes=file_bytes,
                filename=file.filename,
                file_id=file_id
            )
            
            # Save file metadata to database
            audio_file = current_meeting_service.save_audio_file(
                file_id=file_id,
                filename=file.filename,
                file_path=file_path,
                content_type=file.content_type,
                size=len(file_bytes)
            )
        else:
            logger.info("Using fallback storage for file upload")
            # Fallback to in-memory storage
            try:
                file_path = save_mock_audio_file(file_bytes, file.filename, file_id)
            except Exception as e:
                logger.error(f"Mock file save failed: {e}")
                file_path = f"./mock_audio_{file_id}.wav"
                
            uploaded_files[file_id] = {
                "file_id": file_id,
                "filename": file.filename,
                "content_type": getattr(file, 'content_type', 'audio/wav'),
                "size": len(file_bytes),
                "uploaded_at": datetime.now().isoformat(),
                "status": "uploaded",
                "file_path": file_path
            }
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "content_type": getattr(file, 'content_type', 'audio/wav'),
            "size": len(file_bytes),
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded",
            "message": "File uploaded successfully. Use file_id to create a meeting."
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add simplified versions of other endpoints
@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "VoiceLink API server is running",
        "services_available": globals().get('SERVICES_AVAILABLE', False)
    }

@router.get("/analytics/overview", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics_overview():
    """Get comprehensive analytics overview"""
    try:
        # Calculate real analytics from stored meetings
        analytics = calculate_analytics_from_meetings()
        
        return AnalyticsResponse(
            total_meetings=analytics["total_meetings"],
            total_participants=analytics["total_participants"],
            total_minutes_recorded=analytics["total_minutes_recorded"],
            avg_meeting_duration=analytics["avg_meeting_duration"],
            top_speakers=[],
            sentiment_analysis={},
            word_cloud_data=[]
        )
    except Exception as e:
        logging.error(f"Analytics overview failed: {e}")
        return AnalyticsResponse(
            total_meetings=0,
            total_participants=0,
            total_minutes_recorded=0.0,
            avg_meeting_duration=0.0,
            top_speakers=[],
            sentiment_analysis={},
            word_cloud_data=[]
        )
