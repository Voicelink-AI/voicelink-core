"""
Database Models for VoiceLink

SQLAlchemy models for storing session data, transcripts, and generated documents.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class DocumentSession:
    """
    Represents a VoiceLink documentation session
    """
    session_id: str
    audio_file_path: str
    participants: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "processing"  # processing, completed, failed
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing results
    vad_segments: List[Dict] = field(default_factory=list)
    diarization_results: Dict = field(default_factory=dict)
    transcripts: List[Dict] = field(default_factory=list)
    code_context: Dict = field(default_factory=dict)
    llm_outputs: Dict = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AudioTranscript:
    """
    Represents a transcript segment with speaker and timing information
    """
    transcript_id: str
    session_id: str
    start_time: float
    end_time: float
    speaker_id: str
    text: str
    confidence: float
    language: str = "en"
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GeneratedDocument:
    """
    Represents a generated document from the LLM pipeline
    """
    document_id: str
    session_id: str
    document_type: str  # summary, action_items, technical_doc, etc.
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Mock storage class for development
class MockStorage:
    """Mock storage implementation for development"""
    
    def __init__(self):
        self.sessions = {}
        self.transcripts = {}
        self.documents = {}
    
    async def save_session(self, session: DocumentSession):
        """Save session to mock storage"""
        self.sessions[session.session_id] = session
    
    async def get_session(self, session_id: str) -> Optional[DocumentSession]:
        """Get session from mock storage"""
        return self.sessions.get(session_id)
    
    async def save_transcript(self, transcript: AudioTranscript):
        """Save transcript to mock storage"""
        self.transcripts[transcript.transcript_id] = transcript
    
    async def save_document(self, document: GeneratedDocument):
        """Save document to mock storage"""
        self.documents[document.document_id] = document
