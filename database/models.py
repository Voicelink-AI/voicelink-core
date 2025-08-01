"""
Database models for VoiceLink Core
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="processing")
    
    # File information
    audio_file_path = Column(String, nullable=False)
    audio_file_name = Column(String)
    audio_file_size = Column(Integer)
    audio_duration = Column(Float)
    
    # Processing results
    transcript = Column(JSON)
    speakers = Column(JSON)
    technical_terms = Column(JSON)
    processing_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    participants = relationship("MeetingParticipant", back_populates="meeting")
    
class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey("meetings.id"), nullable=False)
    email = Column(String)
    name = Column(String)
    role = Column(String)
    
    # Relationships
    meeting = relationship("Meeting", back_populates="participants")

class AudioFile(Base):
    __tablename__ = "audio_files"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String)
    size = Column(Integer)
    
    # Processing status
    status = Column(String, default="uploaded")  # uploaded, processing, completed, error
    processing_error = Column(Text)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
