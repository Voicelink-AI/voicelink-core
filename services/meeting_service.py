"""
Meeting service for VoiceLink Core - Handles meeting CRUD operations
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class Meeting:
    """Meeting data model"""
    def __init__(
        self,
        meeting_id: str,
        title: str,
        description: Optional[str] = None,
        status: str = "scheduled",
        audio_file_path: Optional[str] = None,
        audio_file_name: Optional[str] = None,
        audio_file_size: Optional[int] = None,
        transcript: Optional[Dict] = None,
        speakers: Optional[List] = None,
        technical_terms: Optional[List] = None,
        created_at: Optional[datetime] = None,
        processed_at: Optional[datetime] = None
    ):
        self.meeting_id = meeting_id
        self.title = title
        self.description = description
        self.status = status
        self.audio_file_path = audio_file_path
        self.audio_file_name = audio_file_name
        self.audio_file_size = audio_file_size
        self.transcript = transcript or {}
        self.speakers = speakers or []
        self.technical_terms = technical_terms or []
        self.created_at = created_at or datetime.now()
        self.processed_at = processed_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert meeting to dictionary"""
        return {
            "meeting_id": self.meeting_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "audio_file_path": self.audio_file_path,
            "audio_file_name": self.audio_file_name,
            "audio_file_size": self.audio_file_size,
            "transcript": self.transcript,
            "speakers": self.speakers,
            "technical_terms": self.technical_terms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None
        }

class MeetingService:
    """Service for managing meetings"""
    
    def __init__(self, storage_path: str = "./data/meetings"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.meetings_file = self.storage_path / "meetings.json"
        self._load_meetings()
    
    def _load_meetings(self):
        """Load meetings from storage"""
        try:
            if self.meetings_file.exists():
                with open(self.meetings_file, 'r') as f:
                    data = json.load(f)
                    self.meetings = {
                        k: Meeting(**v) for k, v in data.items()
                    }
            else:
                self.meetings = {}
            logger.info(f"Loaded {len(self.meetings)} meetings from storage")
        except Exception as e:
            logger.error(f"Failed to load meetings: {e}")
            self.meetings = {}
    
    def _save_meetings(self):
        """Save meetings to storage"""
        try:
            data = {k: v.to_dict() for k, v in self.meetings.items()}
            with open(self.meetings_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save meetings: {e}")
    
    def create_meeting(
        self,
        meeting_id: str,
        title: str,
        description: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        audio_file_name: Optional[str] = None,
        audio_file_size: Optional[int] = None
    ) -> Meeting:
        """Create a new meeting"""
        try:
            meeting = Meeting(
                meeting_id=meeting_id,
                title=title,
                description=description,
                audio_file_path=audio_file_path,
                audio_file_name=audio_file_name,
                audio_file_size=audio_file_size,
                status="processing"
            )
            
            self.meetings[meeting_id] = meeting
            self._save_meetings()
            
            logger.info(f"Created meeting: {meeting_id}")
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            raise
    
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID"""
        return self.meetings.get(meeting_id)
    
    def get_meetings(
        self,
        limit: int = 10,
        status: Optional[str] = None,
        offset: int = 0
    ) -> List[Meeting]:
        """Get meetings with optional filtering"""
        try:
            meetings = list(self.meetings.values())
            
            # Filter by status if provided
            if status:
                meetings = [m for m in meetings if m.status == status]
            
            # Sort by creation time (newest first)
            meetings.sort(key=lambda m: m.created_at, reverse=True)
            
            # Apply pagination
            return meetings[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to get meetings: {e}")
            return []
    
    def update_meeting_results(
        self,
        meeting_id: str,
        transcript: Dict[str, Any],
        speakers: List[Dict],
        technical_terms: List[str],
        audio_duration: Optional[float] = None,
        status: str = "completed",
        processing_error: Optional[str] = None
    ) -> Optional[Meeting]:
        """Update meeting with processing results"""
        try:
            meeting = self.meetings.get(meeting_id)
            if not meeting:
                logger.warning(f"Meeting {meeting_id} not found for update")
                return None
            
            meeting.transcript = transcript
            meeting.speakers = speakers
            meeting.technical_terms = technical_terms
            meeting.status = status
            meeting.processed_at = datetime.now()
            
            if processing_error:
                meeting.processing_error = processing_error
            
            self._save_meetings()
            
            logger.info(f"Updated meeting results: {meeting_id}")
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to update meeting results: {e}")
            return None
    
    def save_audio_file(
        self,
        file_id: str,
        filename: str,
        file_path: str,
        content_type: str,
        size: int
    ) -> Dict[str, Any]:
        """Save audio file metadata"""
        try:
            # This would normally save to a database
            # For now, we'll use a simple file-based approach
            audio_files_file = self.storage_path / "audio_files.json"
            
            try:
                with open(audio_files_file, 'r') as f:
                    audio_files = json.load(f)
            except FileNotFoundError:
                audio_files = {}
            
            audio_files[file_id] = {
                "file_id": file_id,
                "filename": filename,
                "file_path": file_path,
                "content_type": content_type,
                "size": size,
                "uploaded_at": datetime.now().isoformat()
            }
            
            with open(audio_files_file, 'w') as f:
                json.dump(audio_files, f, indent=2)
            
            logger.info(f"Saved audio file metadata: {file_id}")
            return audio_files[file_id]
            
        except Exception as e:
            logger.error(f"Failed to save audio file metadata: {e}")
            raise
