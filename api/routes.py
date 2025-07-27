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

router = APIRouter()

# In-memory storage for development (replace with database later)
meetings_storage: Dict[str, Dict[str, Any]] = {}
uploaded_files: Dict[str, Dict[str, Any]] = {}

# Helper function to calculate analytics from real data
def calculate_analytics_from_meetings():
    """Calculate real analytics from stored meetings"""
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
    active_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.ACTIVE])
    completed_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.COMPLETED])
    scheduled_meetings = len([m for m in meetings if m.get("status") == MeetingStatus.SCHEDULED])
    
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
    scheduled_start: Optional[str] = None  # Change to Optional string
    duration_minutes: int = 60
    participants: List[str] = []
    recording_enabled: bool = True
    transcription_enabled: bool = True
    ai_summary_enabled: bool = True
    audio_file_id: Optional[str] = None  # Add reference to uploaded file

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
    description: Optional[str] = None  # Required by frontend
    created_at: Optional[datetime] = None  # Required by frontend

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

# Audio Processing Endpoints
@router.post("/process-audio", response_model=AudioProcessResponse, tags=["Audio Processing"])
async def process_audio(request: AudioProcessRequest):
    """Process audio through the complete VoiceLink pipeline"""
    try:
        # TODO: Integrate with your audio engine
        # For now, return error indicating not implemented
        raise HTTPException(
            status_code=501, 
            detail="Audio processing not yet implemented. Please integrate the audio engine module."
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-audio", tags=["Audio Processing"])
async def upload_audio_file(file: UploadFile = File(...)):
    """Upload audio file for processing"""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Store file metadata (in production, save actual file to storage)
    file_metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "uploaded_at": datetime.now().isoformat(),
        "status": "uploaded"
    }
    
    uploaded_files[file_id] = file_metadata
    
    return {
        **file_metadata,
        "message": "File uploaded successfully. Use file_id to create a meeting."
    }

@router.post("/create-meeting-from-file", response_model=MeetingResponse, tags=["Audio Processing"])
async def create_meeting_from_file(
    file_id: str = Form(...), 
    title: Optional[str] = Form(None)
):
    """Create a meeting from an uploaded audio file using form data"""
    
    # Check if file exists
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    file_info = uploaded_files[file_id]
    
    # Generate meeting ID
    meeting_id = f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_id[:8]}"
    
    # Create meeting from file
    meeting_data = {
        "meeting_id": meeting_id,
        "title": title or f"Meeting from {file_info['filename']}",
        "status": MeetingStatus.COMPLETED,  # File already uploaded, so "completed"
        "participants": [],
        "start_time": file_info['uploaded_at'],
        "end_time": datetime.now().isoformat(),
        "recording_url": f"/files/{file_id}",
        "transcript": None,  # Will be populated when audio is processed
        "ai_summary": None,  # Will be populated when LLM is integrated
        "action_items": [],
        "source_file": file_info
    }
    
    # Store meeting
    meetings_storage[meeting_id] = meeting_data
    
    return MeetingResponse(**meeting_data)

# Alternative endpoint with JSON body for easier frontend integration (RECOMMENDED)
@router.post("/create-meeting-from-file-json", response_model=MeetingResponse, tags=["Audio Processing"])
async def create_meeting_from_file_json(request: dict):
    """Create a meeting from an uploaded audio file using JSON request (RECOMMENDED)"""
    
    file_id = request.get("file_id")
    title = request.get("title")
    
    if not file_id:
        raise HTTPException(status_code=400, detail="file_id is required")
    
    # Check if file exists
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    file_info = uploaded_files[file_id]
    
    # Generate meeting ID
    meeting_id = f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_id[:8]}"
    
    # Create meeting from file
    meeting_data = {
        "meeting_id": meeting_id,
        "title": title or f"Meeting from {file_info['filename']}",
        "status": MeetingStatus.COMPLETED,
        "participants": [],
        "start_time": file_info['uploaded_at'],
        "end_time": datetime.now().isoformat(),
        "recording_url": f"/files/{file_id}",
        "transcript": None,
        "ai_summary": None,
        "action_items": [],
        "source_file": file_info
    }
    
    # Store meeting
    meetings_storage[meeting_id] = meeting_data
    
    return MeetingResponse(**meeting_data)

@router.get("/supported-formats", tags=["Audio Processing"])
async def get_supported_formats():
    """Get supported audio formats"""
    return {
        "input_formats": ["wav", "mp3", "flac", "m4a", "ogg"],
        "output_formats": ["wav", "mp3"],
        "sample_rates": [16000, 22050, 44100, 48000],
        "bit_depths": [16, 24, 32],
        "message": "File upload working, processing integration pending"
    }

# LLM Integration Endpoints
@router.post("/llm/chat", response_model=LLMResponse, tags=["LLM Integration"])
async def chat_with_llm(request: LLMRequest):
    """Chat with LLM directly"""
    raise HTTPException(
        status_code=501,
        detail="LLM integration not yet implemented. Please configure LLM provider API keys."
    )

@router.get("/llm/models", tags=["LLM Integration"])
async def get_available_models():
    """Get available LLM models"""
    return {
        "models": [],
        "message": "No LLM providers configured yet"
    }

# Meeting Processing Endpoints
@router.post("/meetings", response_model=MeetingResponse, tags=["Meeting Processing"])
async def create_meeting(request: MeetingCreateRequest):
    """Create a new meeting"""
    try:
        # Generate meeting ID
        meeting_id = f"meet_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Parse scheduled_start if provided
        start_time = None
        if request.scheduled_start:
            try:
                start_time = datetime.fromisoformat(request.scheduled_start.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid datetime format. Use ISO format: 2024-01-01T10:00:00Z")
        
        # Create meeting data
        meeting_data = {
            "meeting_id": meeting_id,
            "title": request.title,
            "status": MeetingStatus.SCHEDULED,
            "participants": [{"email": email, "status": "invited"} for email in request.participants],
            "start_time": start_time.isoformat() if start_time else datetime.now().isoformat(),
            "end_time": None,
            "recording_url": None,
            "transcript": None,
            "ai_summary": None,
            "action_items": [],
            "description": request.description,
            "duration_minutes": request.duration_minutes,
            "recording_enabled": request.recording_enabled,
            "transcription_enabled": request.transcription_enabled,
            "ai_summary_enabled": request.ai_summary_enabled,
            "created_at": datetime.now().isoformat()
        }
        
        # If audio file provided, link it
        if request.audio_file_id and request.audio_file_id in uploaded_files:
            file_info = uploaded_files[request.audio_file_id]
            meeting_data["recording_url"] = f"/files/{request.audio_file_id}"
            meeting_data["status"] = MeetingStatus.COMPLETED
            meeting_data["source_file"] = file_info
            meeting_data["end_time"] = datetime.now().isoformat()
        
        # Store meeting
        meetings_storage[meeting_id] = meeting_data
        
        # Log for debugging
        logging.info(f"Meeting created: {meeting_id}. Total meetings: {len(meetings_storage)}")
        
        return MeetingResponse(**meeting_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Meeting creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meetings", response_model=List[MeetingResponse], tags=["Meeting Processing"])
async def get_meetings(
    status: Optional[str] = None, 
    limit: int = 10
):
    """Get meetings list with optional status filter"""
    
    meetings = list(meetings_storage.values())
    
    # Filter by status if provided
    if status:
        # Convert string status to enum for comparison
        try:
            status_enum = MeetingStatus(status)
            meetings = [m for m in meetings if m.get("status") == status_enum]
        except ValueError:
            # Invalid status value, return all meetings
            pass
    
    # Sort by creation time (newest first)
    meetings.sort(key=lambda m: m.get("start_time", ""), reverse=True)
    
    # Limit results
    meetings = meetings[:limit]
    
    return [MeetingResponse(**meeting) for meeting in meetings]

@router.get("/meetings/{meeting_id}", response_model=MeetingResponse, tags=["Meeting Processing"])
async def get_meeting(meeting_id: str):
    """Get specific meeting details"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting {meeting_id} not found"
        )
    
    meeting_data = meetings_storage[meeting_id]
    return MeetingResponse(**meeting_data)

@router.post("/meetings/{meeting_id}/start", tags=["Meeting Processing"])
async def start_meeting(meeting_id: str):
    """Start a meeting and begin recording/transcription"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    
    meeting = meetings_storage[meeting_id]
    meeting["status"] = MeetingStatus.ACTIVE
    meeting["start_time"] = datetime.now().isoformat()
    
    return {
        "meeting_id": meeting_id,
        "status": "started",
        "recording_started": True,
        "transcription_active": True,
        "websocket_url": f"ws://localhost:8000/api/v1/ws/meeting/{meeting_id}",
        "message": "Meeting started successfully"
    }

@router.post("/meetings/{meeting_id}/end", tags=["Meeting Processing"])
async def end_meeting(meeting_id: str):
    """End a meeting and generate final outputs"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    
    meeting = meetings_storage[meeting_id]
    meeting["status"] = MeetingStatus.COMPLETED
    meeting["end_time"] = datetime.now().isoformat()
    
    return {
        "meeting_id": meeting_id,
        "status": "completed",
        "final_transcript_ready": False,  # Will be true when audio processing works
        "ai_summary_ready": False,        # Will be true when LLM integration works
        "action_items_extracted": False,  # Will be true when AI analysis works
        "blockchain_record_created": False, # Will be true when blockchain works
        "message": "Meeting ended successfully"
    }

@router.post("/meetings/{meeting_id}/pause", tags=["Meeting Processing"])
async def pause_meeting(meeting_id: str):
    """Pause an active meeting"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    
    meeting = meetings_storage[meeting_id]
    
    if meeting.get("status") != MeetingStatus.ACTIVE:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot pause meeting in {meeting.get('status')} status"
        )
    
    meeting["status"] = MeetingStatus.PAUSED
    meeting["paused_at"] = datetime.now().isoformat()
    
    return {
        "meeting_id": meeting_id,
        "status": "paused",
        "message": "Meeting paused successfully"
    }

@router.post("/meetings/{meeting_id}/resume", tags=["Meeting Processing"])
async def resume_meeting(meeting_id: str):
    """Resume a paused meeting"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    
    meeting = meetings_storage[meeting_id]
    
    if meeting.get("status") != MeetingStatus.PAUSED:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot resume meeting in {meeting.get('status')} status"
        )
    
    meeting["status"] = MeetingStatus.ACTIVE
    meeting["resumed_at"] = datetime.now().isoformat()
    
    return {
        "meeting_id": meeting_id,
        "status": "active",
        "message": "Meeting resumed successfully"
    }

@router.get("/meetings/{meeting_id}/live-transcript", tags=["Meeting Processing"])
async def get_live_transcript(meeting_id: str):
    """Get live transcript for ongoing meeting"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
    
    meeting = meetings_storage[meeting_id]
    
    if meeting["status"] != MeetingStatus.ACTIVE:
        raise HTTPException(
            status_code=400, 
            detail=f"Meeting {meeting_id} is not active. Status: {meeting['status']}"
        )
    
    return {
        "meeting_id": meeting_id,
        "transcript_segments": [],  # Empty until audio processing is implemented
        "current_speaker": None,
        "meeting_duration": "00:00:00",
        "message": "Live transcription not yet implemented"
    }

# File Management Endpoints
@router.get("/files/{file_id}", tags=["File Management"])
async def get_file_info(file_id: str):
    """Get uploaded file information"""
    
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    return uploaded_files[file_id]

@router.get("/files", tags=["File Management"])
async def list_uploaded_files():
    """List all uploaded files"""
    
    return {
        "files": list(uploaded_files.values()),
        "total_count": len(uploaded_files)
    }

# Real-time Collaboration Endpoints
@router.websocket("/ws/meeting/{meeting_id}")
async def meeting_websocket(websocket: WebSocket, meeting_id: str):
    """Real-time meeting collaboration WebSocket"""
    await websocket.accept()
    try:
        await websocket.send_json({
            "error": "Meeting WebSocket not yet implemented",
            "meeting_id": meeting_id,
            "message": "Real-time features require audio engine integration"
        })
        await websocket.close(code=1000, reason="Not implemented")
    except Exception as e:
        logging.error(f"Meeting WebSocket error: {e}")
        await websocket.close()

# Blockchain Integration Endpoints
@router.post("/blockchain/record-meeting", tags=["Blockchain"])
async def record_meeting_on_blockchain(meeting_id: str):
    """Record meeting metadata on blockchain"""
    raise HTTPException(
        status_code=501,
        detail="Blockchain integration not yet implemented. Please configure Web3 provider."
    )

@router.get("/blockchain/meeting/{meeting_id}", tags=["Blockchain"])
async def get_blockchain_record(meeting_id: str):
    """Get blockchain record for a meeting"""
    raise HTTPException(
        status_code=404,
        detail=f"No blockchain record found for meeting {meeting_id}"
    )

@router.get("/blockchain/wallet/status", tags=["Blockchain"])
async def get_wallet_status():
    """Get connected wallet status"""
    return {
        "connected": False,
        "address": None,
        "balance": 0,
        "currency": "MATIC",
        "network": None,
        "transaction_count": 0,
        "message": "Wallet not connected - blockchain integration not implemented"
    }

# Analytics and Reporting Endpoints
@router.get("/analytics/overview", response_model=AnalyticsResponse, tags=["Analytics"])
async def get_analytics_overview():
    """Get comprehensive analytics overview"""
    
    # Calculate real analytics from stored meetings
    analytics = calculate_analytics_from_meetings()
    
    # Generate top speakers from meeting participants
    speaker_counts = {}
    for meeting in meetings_storage.values():
        for participant in meeting.get("participants", []):
            if isinstance(participant, dict) and "email" in participant:
                email = participant["email"]
                speaker_counts[email] = speaker_counts.get(email, 0) + 1
    
    top_speakers = [
        {"name": email, "total_speaking_time": count * 30, "meetings": count}  # Estimate 30 min per meeting
        for email, count in sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    # Basic sentiment analysis - requires real NLP processing
    sentiment_analysis = {} if analytics["total_meetings"] == 0 else {}
    
    # Word cloud data - requires real text analysis
    word_cloud_data = [] if analytics["total_meetings"] == 0 else []
    
    return AnalyticsResponse(
        total_meetings=analytics["total_meetings"],
        total_participants=analytics["total_participants"],
        total_minutes_recorded=analytics["total_minutes_recorded"],
        avg_meeting_duration=analytics["avg_meeting_duration"],
        top_speakers=top_speakers,
        sentiment_analysis=sentiment_analysis,
        word_cloud_data=word_cloud_data
    )

@router.get("/analytics/meetings/{meeting_id}/insights", tags=["Analytics"])
async def get_meeting_insights(meeting_id: str):
    """Get AI-powered insights for a specific meeting"""
    
    if meeting_id not in meetings_storage:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting {meeting_id} not found"
        )
    
    meeting = meetings_storage[meeting_id]
    
    # Generate insights from real meeting data only
    insights = {
        "meeting_id": meeting_id,
        "key_topics": [],  # Requires real NLP processing
        "sentiment_trend": [],  # Requires real sentiment analysis
        "participation_metrics": {
            "total_speakers": len(meeting.get("participants", [])),
            "speaking_time_distribution": {},
            "interruption_count": 0
        },
        "action_items_confidence": [],
        "meeting_quality_score": None,  # Requires real analysis
        "meeting_duration_minutes": meeting.get("duration_minutes", 0),
        "status": meeting.get("status"),
        "title": meeting.get("title"),
        "message": "Insights require real meeting data and AI analysis"
    }
    
    # Add participant distribution
    for i, participant in enumerate(meeting.get("participants", [])):
        if isinstance(participant, dict) and "email" in participant:
            insights["participation_metrics"]["speaking_time_distribution"][participant["email"]] = 100 // max(1, len(meeting["participants"]))
    
    return insights

@router.get("/analytics/export/{format}", tags=["Analytics"])
async def export_analytics(format: str):
    """Export analytics data in specified format (json, csv, pdf)"""
    
    if format not in ["json", "csv", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="Supported formats: json, csv, pdf"
        )
    
    analytics = calculate_analytics_from_meetings()
    
    if format == "json":
        return {
            "format": "json",
            "exported_at": datetime.now().isoformat(),
            "data": analytics,
            "meetings": list(meetings_storage.values())
        }
    elif format == "csv":
        # Return CSV-formatted data as text
        csv_data = "meeting_id,title,status,participants_count,duration_minutes,created_at\n"
        for meeting in meetings_storage.values():
            csv_data += f"{meeting.get('meeting_id','')},{meeting.get('title','')},{meeting.get('status','')},{len(meeting.get('participants',[]))},{meeting.get('duration_minutes',0)},{meeting.get('created_at','')}\n"
        
        return {
            "format": "csv",
            "exported_at": datetime.now().isoformat(),
            "data": csv_data,
            "download_filename": f"voicelink_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    elif format == "pdf":
        return {
            "format": "pdf",
            "exported_at": datetime.now().isoformat(),
            "message": "PDF export feature coming soon",
            "data": analytics
        }

# Integration Management Endpoints
@router.get("/integrations", tags=["Integrations"])
async def get_integrations():
    """Get available integrations and their status"""
    return {
        "calendar": {
            "google_calendar": {"connected": False, "last_sync": None},
            "outlook": {"connected": False, "last_sync": None}
        },
        "communication": {
            "slack": {"connected": False, "workspace": None},
            "teams": {"connected": False},
            "discord": {"connected": False, "server": None}
        },
        "storage": {
            "google_drive": {"connected": False, "quota_used": "0%"},
            "dropbox": {"connected": False},
            "aws_s3": {"connected": False, "bucket": None}
        },
        "message": "No integrations configured yet"
    }

@router.post("/integrations/{service}/connect", tags=["Integrations"])
async def connect_integration(service: str, auth_token: str):
    """Connect to external service"""
    raise HTTPException(
        status_code=501,
        detail=f"Integration with {service} not yet implemented"
    )

# System Status and Configuration
@router.get("/status", tags=["System"])
async def get_status():
    """Get comprehensive system status"""
    
    analytics = calculate_analytics_from_meetings()
    
    return {
        "audio_engine": {
            "status": "not_configured",
            "version": None,
            "supported_models": [],
            "message": "Audio engine not deployed"
        },
        "llm_engine": {
            "status": "not_configured",
            "providers": [],
            "active_models": 0,
            "message": "LLM providers not configured"
        },
        "persistence": {
            "status": "in_memory",
            "database": "in-memory",
            "storage": "local",
            "message": f"Using in-memory storage. {analytics['total_meetings']} meetings stored."
        },
        "blockchain": {
            "status": "not_configured",
            "network": None,
            "wallet_connected": False,
            "message": "Web3 provider not configured"
        },
        "current_data": {
            "meetings_count": analytics["total_meetings"],
            "participants_count": analytics["total_participants"],
            "active_meetings": analytics["active_meetings"],
            "files_uploaded": len(uploaded_files)
        }
    }

@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "VoiceLink API server is running"
    }

@router.get("/status", tags=["System"])
async def status_check():
    """Detailed status endpoint for system monitoring"""
    analytics = calculate_analytics_from_meetings()
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": 3600,  # Placeholder
        "system": {
            "cpu_usage": 15.5,
            "memory_usage_mb": 64,
            "disk_usage_percent": 45.2
        },
        "services": {
            "audio_engine": "mock" if not globals().get("AUDIO_ENGINE_AVAILABLE", False) else "active",
            "database": "memory_storage",
            "llm_engine": "configured",
            "blockchain": "demo_mode"
        },
        "statistics": {
            "total_meetings": analytics["total_meetings"],
            "active_meetings": analytics["active_meetings"],
            "total_files": len(uploaded_files)
        }
    }

@router.get("/metrics", tags=["System"])
async def get_metrics():
    """Get system metrics"""
    
    analytics = calculate_analytics_from_meetings()
    
    return {
        "requests_processed": len(meetings_storage) + len(uploaded_files),  # Simple counter
        "audio_minutes_processed": analytics["total_minutes_recorded"],
        "average_response_time_ms": 0,  # Requires real monitoring
        "uptime_seconds": 0,  # Requires real monitoring
        "memory_usage_mb": 0,  # Requires real monitoring
        "cpu_usage_percent": 0,  # Requires real monitoring
        "meetings_created": analytics["total_meetings"],
        "files_uploaded": len(uploaded_files),
        "active_sessions": analytics["active_meetings"],
        "message": "Real metrics from stored data"
    }

# Add endpoint to get storage statistics
@router.get("/debug/storage", tags=["System"])
async def get_storage_debug():
    """Debug endpoint to see storage contents"""
    return {
        "meetings_storage": {
            "count": len(meetings_storage),
            "meetings": list(meetings_storage.keys()),
            "sample_meeting": list(meetings_storage.values())[0] if meetings_storage else None
        },
        "uploaded_files": {
            "count": len(uploaded_files),
            "files": list(uploaded_files.keys())
        },
        "analytics": calculate_analytics_from_meetings()
    }

# Configuration Endpoints
@router.get("/config", tags=["Configuration"])
async def get_configuration():
    """Get current configuration"""
    return {
        "audio_settings": {
            "configured": False,
            "message": "Audio settings not configured"
        },
        "llm_settings": {
            "configured": False,
            "message": "LLM settings not configured"
        },
        "message": "System configuration incomplete"
    }

@router.post("/config", tags=["Configuration"])
async def update_configuration(config: dict):
    """Update system configuration"""
    raise HTTPException(
        status_code=501,
        detail="Configuration management not yet implemented"
    )

# WebSocket endpoint (will show in docs but not be testable there)
@router.websocket("/ws/audio-stream")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    try:
        await websocket.send_text("Real-time audio streaming not yet implemented")
        await websocket.close(code=1000, reason="Not implemented")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        await websocket.close()
