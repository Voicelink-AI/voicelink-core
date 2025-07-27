"""
Meeting API Routes - Updated for Frontend Compatibility

FastAPI routes that match the frontend API contract exactly.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import uuid
from datetime import datetime
import json
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import VoiceLink components
try:
    from core.orchestrator import VoiceLinkOrchestrator
    from api.config import Config
    from analytics.service import analytics_service
    from persistence.database_service import get_database_service
    VOICELINK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"VoiceLink components not available: {e}")
    VOICELINK_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["meetings"])

# Mock database - replace with real database service
meetings_db = {}
uploaded_files = {}

# Initialize VoiceLink components
orchestrator = None
db_service = None

if VOICELINK_AVAILABLE:
    try:
        config = Config()
        orchestrator_config = Config.get_llm_config()
        orchestrator_config.update({
            "whisper_model": Config.WHISPER_MODEL,
            "vosk_model_path": Config.VOSK_MODEL_PATH,
            "huggingface_token": Config.HUGGINGFACE_TOKEN
        })
        orchestrator = VoiceLinkOrchestrator(orchestrator_config)
        db_service = get_database_service()
        logger.info("✅ VoiceLink orchestrator and database service initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize VoiceLink components: {e}")
        orchestrator = None
        db_service = None

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for frontend polling"""
    return {
        "status": "healthy",
        "service": "voicelink-core",
        "version": "1.0.0",
        "components": {
            "orchestrator": orchestrator is not None,
            "database": db_service is not None,
            "analytics": analytics_service is not None,
            "voicelink_available": VOICELINK_AVAILABLE
        },
        "capabilities": {
            "audio_processing": orchestrator is not None,
            "real_time_analytics": True,
            "database_storage": db_service is not None
        }
    }

@router.get("/meetings")
async def get_meetings(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: Optional[int] = Query(10, description="Number of meetings to return"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
) -> Dict[str, Any]:
    """Get list of meetings with optional filtering"""
    try:
        meetings = list(meetings_db.values())
        
        # Filter by status if provided
        if status:
            meetings = [m for m in meetings if m.get("status") == status]
        
        # Apply pagination
        total = len(meetings)
        meetings = meetings[offset:offset + limit]
        
        return {
            "meetings": meetings,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error fetching meetings: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to fetch meetings: {e}"})

@router.post("/meetings")
async def create_meeting(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    participants: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Create a new meeting"""
    try:
        meeting_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Parse participants
        participant_list = []
        if participants:
            participant_list = [p.strip() for p in participants.split(",")]
        
        meeting = {
            "meeting_id": meeting_id,
            "title": title,
            "description": description or "",
            "status": "created",
            "participants": participant_list,
            "start_time": None,
            "end_time": None,
            "recording_url": None,
            "transcript": None,
            "ai_summary": None,
            "action_items": [],
            "created_at": now.isoformat(),
        }
        
        meetings_db[meeting_id] = meeting
        
        return meeting
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to create meeting: {e}"})

@router.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str) -> Dict[str, Any]:
    """Get a specific meeting by ID"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    return meetings_db[meeting_id]

@router.post("/meetings/{meeting_id}/start")
async def start_meeting(meeting_id: str) -> Dict[str, Any]:
    """Start a meeting"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    meeting = meetings_db[meeting_id]
    meeting["status"] = "active"
    meeting["start_time"] = datetime.utcnow().isoformat()
    
    return meeting

@router.post("/meetings/{meeting_id}/end")
async def end_meeting(meeting_id: str) -> Dict[str, Any]:
    """End a meeting"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    meeting = meetings_db[meeting_id]
    meeting["status"] = "completed"
    meeting["end_time"] = datetime.utcnow().isoformat()
    
    return meeting

@router.post("/meetings/{meeting_id}/pause")
async def pause_meeting(meeting_id: str) -> Dict[str, Any]:
    """Pause a meeting"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    meeting = meetings_db[meeting_id]
    meeting["status"] = "paused"
    
    return meeting

@router.post("/meetings/{meeting_id}/resume")
async def resume_meeting(meeting_id: str) -> Dict[str, Any]:
    """Resume a paused meeting"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    meeting = meetings_db[meeting_id]
    meeting["status"] = "active"
    
    return meeting

@router.get("/meetings/{meeting_id}/processing-status")
async def get_processing_status(meeting_id: str) -> Dict[str, Any]:
    """Get the processing status of a meeting"""
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail={"message": "Meeting not found"})
    
    meeting = meetings_db[meeting_id]
    status = meeting.get("status", "unknown")
    
    return {
        "meeting_id": meeting_id,
        "status": status,
        "processing_stage": meeting.get("processing_stage", None),
        "progress": _get_progress_percentage(status, meeting.get("processing_stage")),
        "estimated_time_remaining": _get_estimated_time(status, meeting.get("processing_stage")),
        "error": meeting.get("error", None),
        "start_time": meeting.get("start_time"),
        "end_time": meeting.get("end_time"),
        "has_transcript": bool(meeting.get("transcript")),
        "has_summary": bool(meeting.get("ai_summary")),
        "has_action_items": bool(meeting.get("action_items")),
        "voicelink_enabled": orchestrator is not None
    }

def _get_progress_percentage(status: str, processing_stage: Optional[str]) -> int:
    """Calculate progress percentage based on status and stage"""
    if status == "created":
        return 0
    elif status == "processing":
        if processing_stage == "audio_analysis":
            return 25
        elif processing_stage == "transcription":
            return 50
        elif processing_stage == "llm_processing":
            return 75
        else:
            return 30
    elif status == "completed":
        return 100
    elif status == "failed":
        return 0
    else:
        return 0

def _get_estimated_time(status: str, processing_stage: Optional[str]) -> Optional[str]:
    """Get estimated time remaining for processing"""
    if status == "processing":
        if processing_stage == "audio_analysis":
            return "2-3 minutes"
        elif processing_stage == "transcription":
            return "1-2 minutes"
        elif processing_stage == "llm_processing":
            return "30-60 seconds"
        else:
            return "2-5 minutes"
    return None

@router.post("/upload-audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
) -> Dict[str, Any]:
    """Upload audio file for processing"""
    try:
        # Validate file type
        if not audio_file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac')):
            raise HTTPException(
                status_code=400, 
                detail={"message": "Invalid audio file format. Supported: WAV, MP3, M4A, FLAC"}
            )
        
        file_id = str(uuid.uuid4())
        
        # Save file temporarily
        temp_dir = Path(tempfile.gettempdir())
        temp_file_path = temp_dir / f"voicelink_{file_id}_{audio_file.filename}"
        
        with open(temp_file_path, "wb") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
        
        # Store file info
        uploaded_files[file_id] = {
            "file_id": file_id,
            "filename": audio_file.filename,
            "path": str(temp_file_path),
            "size": len(content),
            "upload_time": datetime.utcnow().isoformat(),
            "status": "uploaded"
        }
        
        return {
            "file_id": file_id,
            "filename": audio_file.filename,
            "status": "uploaded",
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to upload audio: {e}"})

@router.post("/create-meeting-from-file-json")
async def create_meeting_from_file(
    background_tasks: BackgroundTasks,
    file_id: str = Form(...),
    title: str = Form(...)
) -> Dict[str, Any]:
    """Create meeting from uploaded audio file"""
    try:
        if file_id not in uploaded_files:
            raise HTTPException(status_code=404, detail={"message": "File not found"})
        
        file_info = uploaded_files[file_id]
        
        # Create meeting
        meeting_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        meeting = {
            "meeting_id": meeting_id,
            "title": title,
            "description": f"Meeting created from audio file: {file_info['filename']}",
            "status": "processing",
            "participants": [],
            "start_time": now.isoformat(),
            "end_time": None,
            "recording_url": file_info['path'],
            "transcript": None,
            "ai_summary": None,
            "action_items": [],
            "created_at": now.isoformat(),
        }
        
        meetings_db[meeting_id] = meeting
        
        # Start processing in background
        background_tasks.add_task(process_audio_file, meeting_id, file_info['path'])
        
        return meeting
        
    except Exception as e:
        logger.error(f"Error creating meeting from file: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to create meeting: {e}"})

async def process_audio_file(meeting_id: str, file_path: str):
    """Background task to process audio file through VoiceLink pipeline"""
    try:
        logger.info(f"🎵 Starting audio processing for meeting {meeting_id}")
        
        if not orchestrator:
            logger.warning("⚠️ Orchestrator not available, using mock processing")
            await _process_audio_mock(meeting_id, file_path)
            return
            
        # Update meeting status to processing
        if meeting_id in meetings_db:
            meetings_db[meeting_id]["status"] = "processing"
            meetings_db[meeting_id]["processing_stage"] = "audio_analysis"
        
        # Process audio through VoiceLink orchestrator
        logger.info(f"🔊 Processing audio file: {file_path}")
        
        # Read audio file
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        # Process through orchestrator
        processing_results = await orchestrator.process_audio(
            audio_data=audio_data,
            audio_format="wav",  # Assume WAV for now, could be detected
            meeting_metadata={
                "meeting_id": meeting_id,
                "participants": meetings_db.get(meeting_id, {}).get("participants", []),
                "title": meetings_db.get(meeting_id, {}).get("title", "Untitled Meeting")
            }
        )
        
        logger.info(f"✅ Audio processing completed for meeting {meeting_id}")
        
        # Update meeting with results
        if meeting_id in meetings_db:
            meeting = meetings_db[meeting_id]
            meeting.update({
                "status": "completed",
                "end_time": datetime.utcnow().isoformat(),
                "processing_stage": "completed",
                "transcript": processing_results.get("transcripts", []),
                "ai_summary": processing_results.get("summary", {}),
                "action_items": processing_results.get("action_items", []),
                "participants_analysis": processing_results.get("participants", []),
                "duration_seconds": processing_results.get("audio_duration", 0)
            })
        
        # Store in database if available
        if db_service:
            try:
                logger.info(f"💾 Storing meeting data in database")
                
                # Create meeting record
                meeting_data = meetings_db.get(meeting_id, {})
                meeting_data['audio_file_path'] = file_path
                meeting_data['audio_duration'] = processing_results.get("audio_duration", 0)
                
                db_meeting_id = db_service.create_meeting(meeting_data)
                
                # Save transcripts
                if processing_results.get("transcripts"):
                    transcript_ids = db_service.save_transcripts(db_meeting_id, processing_results["transcripts"])
                    logger.info(f"💾 Saved {len(transcript_ids)} transcript segments")
                
                # Save analysis
                if processing_results.get("summary") or processing_results.get("action_items"):
                    analysis_data = {
                        "summary": processing_results.get("summary", {}),
                        "action_items": processing_results.get("action_items", []),
                        "key_points": processing_results.get("key_points", []),
                        "llm_provider": "voicelink_orchestrator"
                    }
                    analysis_id = db_service.save_meeting_analysis(db_meeting_id, analysis_data)
                    logger.info(f"💾 Saved meeting analysis: {analysis_id}")
                
                # Update meeting status
                db_service.update_meeting_status(db_meeting_id, 'completed')
                
                # Queue for analytics processing
                await analytics_service.queue_meeting_for_analytics(db_meeting_id)
                logger.info(f"📊 Queued meeting for analytics processing")
                
            except Exception as db_error:
                logger.error(f"❌ Database storage failed: {db_error}")
        
        logger.info(f"🎉 Meeting {meeting_id} processing completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error processing audio for meeting {meeting_id}: {e}")
        if meeting_id in meetings_db:
            meetings_db[meeting_id]["status"] = "failed"
            meetings_db[meeting_id]["error"] = str(e)

async def _process_audio_mock(meeting_id: str, file_path: str):
    """Fallback mock processing when orchestrator is not available"""
    logger.info(f"🎭 Using mock processing for meeting {meeting_id}")
    
    # Simulate processing time
    import asyncio
    await asyncio.sleep(2)
    
    # Update meeting with mock results
    if meeting_id in meetings_db:
        meeting = meetings_db[meeting_id]
        meeting.update({
            "status": "completed",
            "end_time": datetime.utcnow().isoformat(),
            "transcript": [
                {
                    "speaker": "Speaker 1",
                    "text": "Welcome to today's meeting. Let's discuss the project updates.",
                    "start_time": 0.0,
                    "end_time": 5.0
                },
                {
                    "speaker": "Speaker 2", 
                    "text": "Thank you. I have several updates to share about our recent progress.",
                    "start_time": 5.0,
                    "end_time": 10.0
                }
            ],
            "ai_summary": {
                "executive_summary": "Team meeting discussing project progress and upcoming milestones.",
                "key_topics": ["Project updates", "Timeline review", "Next steps"],
                "duration_minutes": 15
            },
            "action_items": [
                {
                    "task": "Complete documentation review",
                    "assignee": "Team Lead",
                    "due_date": "2025-01-30"
                }
            ]
        })

@router.get("/analytics/overview")
async def get_analytics_overview() -> Dict[str, Any]:
    """Get analytics overview data"""
    try:
        total_meetings = len(meetings_db)
        completed_meetings = len([m for m in meetings_db.values() if m.get("status") == "completed"])
        active_meetings = len([m for m in meetings_db.values() if m.get("status") == "active"])
        
        # Calculate real average duration from meetings with actual duration data
        durations = []
        for meeting in meetings_db.values():
            if meeting.get("start_time") and meeting.get("end_time"):
                try:
                    start = datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00'))
                    end = datetime.fromisoformat(meeting["end_time"].replace('Z', '+00:00'))
                    duration_minutes = (end - start).total_seconds() / 60
                    durations.append(duration_minutes)
                except:
                    pass
        
        average_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total_meetings": total_meetings,
            "completed_meetings": completed_meetings,
            "active_meetings": active_meetings,
            "processing_meetings": len([m for m in meetings_db.values() if m.get("status") == "processing"]),
            "total_participants": sum(len(m.get("participants", [])) for m in meetings_db.values()),
            "average_duration_minutes": round(average_duration, 1),
            "charts": {
                "meetings_per_day": [],  # Requires real data aggregation
                "status_distribution": [
                    {"status": "completed", "count": completed_meetings},
                    {"status": "active", "count": active_meetings},
                    {"status": "processing", "count": total_meetings - completed_meetings - active_meetings}
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to fetch analytics: {e}"})

@router.get("/analytics/export/{format}")
async def export_analytics(format: str) -> Dict[str, Any]:
    """Export analytics data in specified format"""
    try:
        if format not in ["json", "csv", "xlsx"]:
            raise HTTPException(status_code=400, detail={"message": "Unsupported export format"})
        
        # Generate real export data
        export_data = {
            "export_id": str(uuid.uuid4()),
            "format": format,
            "status": "pending",  # Real export would be pending processing
            "download_url": None,  # No download available without real data processing
            "created_at": datetime.utcnow().isoformat(),
            "message": "Export requires real analytics data processing"
        }
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to export analytics: {e}"})
