"""
SQLAlchemy Database Models for VoiceLink

Defines the database schema for storing meeting data, transcripts, and analysis results.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Meeting(Base):
    """Meeting session record"""
    __tablename__ = 'meetings'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String, default='processing')  # processing, completed, failed
    participants = Column(JSON)  # List of participant names/emails
    meeting_metadata = Column(JSON)  # Additional meeting metadata
    
    # Audio processing info
    audio_file_path = Column(String)
    audio_duration = Column(Float)  # Duration in seconds
    
    # Processing results
    transcripts = relationship("Transcript", back_populates="meeting")
    analysis = relationship("MeetingAnalysis", back_populates="meeting", uselist=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Transcript(Base):
    """Individual transcript segments"""
    __tablename__ = 'transcripts'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
    
    # Transcript data
    speaker = Column(String)
    text = Column(Text, nullable=False)
    confidence = Column(Float)  # ASR confidence score
    
    # Timing information
    start_time = Column(Float)  # Seconds from meeting start
    end_time = Column(Float)
    
    # Speaker diarization info
    speaker_id = Column(String)  # Internal speaker ID
    
    # Language and processing info
    language = Column(String, default='en')
    processing_method = Column(String)  # whisper, vosk, etc.
    
    meeting = relationship("Meeting", back_populates="transcripts")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MeetingAnalysis(Base):
    """LLM analysis results for a meeting"""
    __tablename__ = 'meeting_analysis'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
    
    # LLM processing results
    summary = Column(JSON)  # Meeting summary with executive summary, topics
    action_items = Column(JSON)  # Extracted action items
    key_points = Column(JSON)  # Key discussion points
    code_analysis = Column(JSON)  # Code context analysis if applicable
    
    # Processing metadata
    llm_provider = Column(String)  # openai, vertexai, etc.
    processing_time = Column(DateTime)
    token_usage = Column(JSON)  # Token usage statistics
    
    # Quality metrics
    confidence_score = Column(Float)
    processing_duration = Column(Float)  # Processing time in seconds
    
    meeting = relationship("Meeting", back_populates="analysis")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ActionItem(Base):
    """Individual action items extracted from meetings"""
    __tablename__ = 'action_items'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
    
    # Action item details
    title = Column(String, nullable=False)
    description = Column(Text)
    assignee = Column(String)
    priority = Column(String, default='medium')  # high, medium, low
    status = Column(String, default='open')  # open, in_progress, completed, cancelled
    
    # Timing
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Context
    source_transcript_id = Column(String, ForeignKey('transcripts.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CodeContext(Base):
    """Code context extracted from meetings"""
    __tablename__ = 'code_context'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
    
    # Code details
    file_path = Column(String)
    language = Column(String)
    code_snippet = Column(Text)
    
    # Analysis results
    functions = Column(JSON)  # Extracted functions/methods
    classes = Column(JSON)   # Extracted classes
    dependencies = Column(JSON)  # Dependencies and imports
    documentation = Column(Text)  # Generated documentation
    
    # Metadata
    extraction_method = Column(String)  # manual, automatic
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Integration(Base):
    """External integration records"""
    __tablename__ = 'integrations'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
    
    # Integration details
    platform = Column(String, nullable=False)  # discord, github, notion, slack
    integration_type = Column(String)  # notification, document_creation, etc.
    
    # Platform-specific data
    external_id = Column(String)  # External platform ID
    external_url = Column(String)  # URL to external resource
    platform_data = Column(JSON)  # Platform-specific metadata
    
    # Status
    status = Column(String, default='pending')  # pending, success, failed
    error_message = Column(Text)
    
    # Timing
    triggered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User info
    user_id = Column(String)
    session_token = Column(String, unique=True)
    
    # Session data
    preferences = Column(JSON)
    activity_log = Column(JSON)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
