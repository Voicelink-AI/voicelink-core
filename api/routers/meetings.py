"""
Meeting API Routes

FastAPI routes for handling meeting processing and documentation generation.
"""

import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
from pathlib import Path
import tempfile
import uuid

from api.utils import create_response, create_error_response, validate_audio_file
from core.orchestrator import VoiceLinkOrchestrator
from api.config import Config
from persistence.database_service import get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

# Initialize orchestrator and database service
config = Config()
orchestrator = VoiceLinkOrchestrator(config)
db_service = get_database_service()


@router.post("/process")
async def process_meeting_audio(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    participants: Optional[str] = Form(None),
    meeting_type: Optional[str] = Form("general"),
    session_id: Optional[str] = Form(None)
):
    """
    Process meeting audio file through VoiceLink pipeline
    
    Args:
        audio_file: Audio file upload (WAV, MP3, M4A, FLAC)
        participants: Comma-separated list of participant names
        meeting_type: Type of meeting (sprint_planning, code_review, etc.)
        session_id: Optional custom session ID
        
    Returns:
        Processing status and session information
    """
    try:
        logger.info(f"Received audio upload: {audio_file.filename}")
        
        # Validate audio file
        if not validate_audio_file(audio_file.filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file format. Supported: WAV, MP3, M4A, FLAC"
            )
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Parse participants
        participant_list = []
        if participants:
            participant_list = [p.strip() for p in participants.split(",")]
        
        # Save uploaded file temporarily
        temp_dir = Path(tempfile.gettempdir())
        temp_file_path = temp_dir / f"voicelink_{session_id}_{audio_file.filename}"
        
        with open(temp_file_path, "wb") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
        
        # Prepare metadata
        metadata = {
            "meeting_type": meeting_type,
            "original_filename": audio_file.filename,
            "file_size": len(content),
            "upload_timestamp": logger.info("Processing audio file")
        }
        
        # Start processing in background
        background_tasks.add_task(
            process_audio_background,
            temp_file_path,
            session_id,
            participant_list,
            metadata
        )
        
        return create_response(
            data={
                "session_id": session_id,
                "status": "processing",
                "participants": participant_list,
                "meeting_type": meeting_type
            },
            message="Audio processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        return create_error_response(
            message="Failed to process audio file",
            error_code="PROCESSING_FAILED",
            details={"error": str(e)}
        )


async def process_audio_background(
    audio_file_path: Path,
    session_id: str,
    participants: List[str],
    metadata: Dict[str, Any]
):
    """Background task for audio processing"""
    try:
        logger.info(f"Starting background processing for session {session_id}")
        
        # Process through VoiceLink pipeline
        session = await orchestrator.process_audio_session(
            audio_file=audio_file_path,
            session_id=session_id,
            participants=participants,
            metadata=metadata
        )
        
        logger.info(f"Background processing completed for session {session_id}")
        
        # Clean up temporary file
        if audio_file_path.exists():
            audio_file_path.unlink()
        
    except Exception as e:
        logger.error(f"Background processing failed for session {session_id}: {e}")


@router.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """
    Get processing status for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Current processing status and results (if completed)
    """
    try:
        # This would query actual storage/database
        # For now, return mock status
        
        return create_response(
            data={
                "session_id": session_id,
                "status": "completed",  # processing, completed, failed
                "progress": {
                    "vad_complete": True,
                    "diarization_complete": True,
                    "transcription_complete": True,
                    "code_context_complete": True,
                    "llm_processing_complete": True,
                    "integration_complete": True
                },
                "results_available": True
            },
            message="Session status retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        return create_error_response(
            message="Failed to retrieve session status",
            error_code="STATUS_RETRIEVAL_FAILED"
        )


@router.get("/results/{session_id}")
async def get_session_results(session_id: str):
    """
    Get processing results for a completed session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Complete processing results including summary, action items, etc.
    """
    try:
        # This would query actual storage/database for session results
        # For now, return mock results
        
        mock_results = {
            "session_id": session_id,
            "processing_completed": True,
            "audio_info": {
                "duration": 185.3,
                "speakers_detected": 3,
                "language": "en"
            },
            "meeting_summary": {
                "executive_summary": "Team discussed API redesign and sprint planning priorities for the next iteration.",
                "main_topics": [
                    "API redesign architecture and security improvements",
                    "Authentication middleware updates and OAuth integration",
                    "Database migration strategy and backwards compatibility"
                ],
                "key_decisions": [
                    "Prioritize authentication middleware in next sprint",
                    "Review PR #234 by end of week",
                    "Schedule database migration for next release"
                ]
            },
            "action_items": [
                {
                    "id": "action_1",
                    "description": "Review and merge PR #234 for authentication middleware",
                    "assignee": "Alice",
                    "deadline": "End of week",
                    "priority": "high"
                },
                {
                    "id": "action_2",
                    "description": "Create migration scripts for user service database",
                    "assignee": "Bob",
                    "deadline": "Next sprint",
                    "priority": "medium"
                }
            ],
            "key_points": [
                "API redesign should prioritize security and performance",
                "Current authentication system has scalability issues",
                "Database migrations need to be backwards compatible"
            ],
            "code_context": {
                "files_mentioned": ["user_service.py", "auth_middleware.py"],
                "pr_references": ["#234"],
                "functions_discussed": ["authenticate_user", "migrate_database"]
            },
            "transcripts": [
                {
                    "start_time": 0.0,
                    "end_time": 5.2,
                    "speaker": "SPEAKER_00",
                    "text": "Let's start the sprint planning meeting. We need to discuss the API redesign."
                }
            ]
        }
        
        return create_response(
            data=mock_results,
            message="Session results retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to get session results: {e}")
        return create_error_response(
            message="Failed to retrieve session results",
            error_code="RESULTS_RETRIEVAL_FAILED"
        )


@router.post("/ask/{session_id}")
async def ask_question(session_id: str, question: str = Form(...)):
    """
    Ask a question about the meeting content using Q&A
    
    Args:
        session_id: Session identifier
        question: Question to ask about the meeting
        
    Returns:
        Answer based on meeting content
    """
    try:
        logger.info(f"Q&A question for session {session_id}: {question}")
        
        # This would use the actual Q&A system with embeddings
        # For now, return mock answer
        
        mock_answer = {
            "question": question,
            "answer": "Based on the meeting discussion, the team decided to prioritize authentication middleware updates in the next sprint, with Alice taking ownership of reviewing PR #234.",
            "confidence": 0.85,
            "sources": [
                "SPEAKER_01: I think we should focus on the authentication middleware first.",
                "SPEAKER_00: Alice, can you review PR #234 by end of week?"
            ]
        }
        
        return create_response(
            data=mock_answer,
            message="Question answered"
        )
        
    except Exception as e:
        logger.error(f"Q&A failed: {e}")
        return create_error_response(
            message="Failed to answer question",
            error_code="QA_FAILED"
        )


@router.get("/sessions")
async def list_sessions(limit: int = 10, offset: int = 0):
    """
    List recent processing sessions
    
    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip
        
    Returns:
        List of recent sessions with basic info
    """
    try:
        # This would query actual database
        # For now, return mock sessions
        
        mock_sessions = [
            {
                "session_id": "session_123",
                "status": "completed",
                "created_at": "2025-07-22T10:30:00Z",
                "duration": 185.3,
                "participants": ["Alice", "Bob", "Charlie"],
                "meeting_type": "sprint_planning"
            },
            {
                "session_id": "session_124", 
                "status": "processing",
                "created_at": "2025-07-22T11:15:00Z",
                "duration": None,
                "participants": ["David", "Eve"],
                "meeting_type": "code_review"
            }
        ]
        
        return create_response(
            data={
                "sessions": mock_sessions,
                "total": len(mock_sessions),
                "limit": limit,
                "offset": offset
            },
            message="Sessions retrieved"
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return create_error_response(
            message="Failed to retrieve sessions",
            error_code="SESSIONS_RETRIEVAL_FAILED"
        )


# Database-aware endpoints

@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get meeting details by ID"""
    try:
        meeting = db_service.get_meeting(meeting_id)
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        return create_response(
            data=meeting,
            message="Meeting retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get meeting {meeting_id}: {e}")
        return create_error_response(
            message="Failed to retrieve meeting",
            error_code="MEETING_RETRIEVAL_FAILED"
        )


@router.get("/{meeting_id}/transcripts")
async def get_meeting_transcripts(meeting_id: str):
    """Get transcripts for a meeting"""
    try:
        transcripts = db_service.get_meeting_transcripts(meeting_id)
        
        return create_response(
            data={
                "meeting_id": meeting_id,
                "transcripts": transcripts,
                "total_segments": len(transcripts)
            },
            message="Transcripts retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get transcripts for meeting {meeting_id}: {e}")
        return create_error_response(
            message="Failed to retrieve transcripts",
            error_code="TRANSCRIPTS_RETRIEVAL_FAILED"
        )


@router.get("/{meeting_id}/analysis")
async def get_meeting_analysis(meeting_id: str):
    """Get LLM analysis results for a meeting"""
    try:
        analysis = db_service.get_meeting_analysis(meeting_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return create_response(
            data=analysis,
            message="Analysis retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis for meeting {meeting_id}: {e}")
        return create_error_response(
            message="Failed to retrieve analysis",
            error_code="ANALYSIS_RETRIEVAL_FAILED"
        )


@router.get("/")
async def list_meetings(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List recent meetings with pagination"""
    try:
        meetings = db_service.list_recent_meetings(limit)
        
        return create_response(
            data={
                "meetings": meetings,
                "total": len(meetings),
                "limit": limit,
                "offset": offset
            },
            message="Meetings retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to list meetings: {e}")
        return create_error_response(
            message="Failed to retrieve meetings",
            error_code="MEETINGS_LIST_FAILED"
        )


@router.get("/stats/overview")
async def get_statistics():
    """Get database statistics and overview"""
    try:
        stats = db_service.get_statistics()
        
        # Add database health check
        db_healthy = db_service.health_check()
        stats['database_healthy'] = db_healthy
        
        return create_response(
            data=stats,
            message="Statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return create_error_response(
            message="Failed to retrieve statistics",
            error_code="STATISTICS_RETRIEVAL_FAILED"
        )
