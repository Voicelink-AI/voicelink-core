"""
Database Service for VoiceLink

Provides database operations and connection management using SQLAlchemy.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from datetime import datetime

from .models.database_models import (
    Base, Meeting, Transcript, MeetingAnalysis, 
    ActionItem, CodeContext, Integration, UserSession
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for managing VoiceLink data"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database service
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'sqlite:///voicelink.db'
        )
        
        # Create engine with appropriate settings
        if self.database_url.startswith('sqlite'):
            self.engine = create_engine(
                self.database_url,
                echo=os.getenv('DEBUG', 'false').lower() == 'true'
            )
        else:
            self.engine = create_engine(
                self.database_url,
                echo=os.getenv('DEBUG', 'false').lower() == 'true',
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=self.engine
        )
        
        # Create tables
        self.create_tables()
        
        logger.info(f"Database service initialized: {self.database_url}")
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    from typing import Generator

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # Meeting operations
    
    def create_meeting(self, meeting_data: Dict[str, Any]) -> str:
        """
        Create a new meeting record
        
        Args:
            meeting_data: Meeting information
            
        Returns:
            Meeting ID
        """
        try:
            with self.get_session() as session:
                meeting = Meeting(
                    title=meeting_data.get('title', 'Untitled Meeting'),
                    description=meeting_data.get('description'),
                    participants=meeting_data.get('participants', []),
                    meeting_metadata=meeting_data.get('metadata', {}),
                    audio_file_path=meeting_data.get('audio_file_path'),
                    audio_duration=meeting_data.get('audio_duration')
                )
                
                session.add(meeting)
                session.flush()  # Get the ID
                
                meeting_id = meeting.id
                logger.info(f"Created meeting: {meeting_id}")
                return meeting_id
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create meeting: {e}")
            raise
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting by ID"""
        try:
            with self.get_session() as session:
                meeting = session.query(Meeting).filter(
                    Meeting.id == meeting_id
                ).first()
                
                if not meeting:
                    return None
                
                return {
                    'id': meeting.id,
                    'title': meeting.title,
                    'description': meeting.description,
                    'start_time': meeting.start_time.isoformat() if meeting.start_time else None,
                    'end_time': meeting.end_time.isoformat() if meeting.end_time else None,
                    'status': meeting.status,
                    'participants': meeting.participants,
                    'metadata': meeting.meeting_metadata,
                    'audio_file_path': meeting.audio_file_path,
                    'audio_duration': meeting.audio_duration,
                    'created_at': meeting.created_at.isoformat(),
                    'updated_at': meeting.updated_at.isoformat()
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get meeting {meeting_id}: {e}")
            return None
    
    def update_meeting_status(self, meeting_id: str, status: str) -> bool:
        """Update meeting processing status"""
        try:
            with self.get_session() as session:
                meeting = session.query(Meeting).filter(
                    Meeting.id == meeting_id
                ).first()
                
                if meeting:
                    meeting.status = status
                    meeting.updated_at = datetime.utcnow()
                    logger.info(f"Updated meeting {meeting_id} status to {status}")
                    return True
                
                return False
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to update meeting status: {e}")
            return False
    
    # Transcript operations
    
    def save_transcripts(self, meeting_id: str, transcripts: List[Dict[str, Any]]) -> List[str]:
        """Save transcript segments for a meeting"""
        try:
            with self.get_session() as session:
                transcript_ids = []
                
                for transcript_data in transcripts:
                    transcript = Transcript(
                        meeting_id=meeting_id,
                        speaker=transcript_data.get('speaker'),
                        text=transcript_data.get('text', ''),
                        confidence=transcript_data.get('confidence'),
                        start_time=transcript_data.get('start_time'),
                        end_time=transcript_data.get('end_time'),
                        speaker_id=transcript_data.get('speaker_id'),
                        language=transcript_data.get('language', 'en'),
                        processing_method=transcript_data.get('processing_method')
                    )
                    
                    session.add(transcript)
                    session.flush()
                    transcript_ids.append(transcript.id)
                
                logger.info(f"Saved {len(transcript_ids)} transcripts for meeting {meeting_id}")
                return transcript_ids
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to save transcripts: {e}")
            raise
    
    def get_meeting_transcripts(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a meeting"""
        try:
            with self.get_session() as session:
                transcripts = session.query(Transcript).filter(
                    Transcript.meeting_id == meeting_id
                ).order_by(Transcript.start_time).all()
                
                return [
                    {
                        'id': t.id,
                        'speaker': t.speaker,
                        'text': t.text,
                        'confidence': t.confidence,
                        'start_time': t.start_time,
                        'end_time': t.end_time,
                        'speaker_id': t.speaker_id,
                        'language': t.language,
                        'processing_method': t.processing_method,
                        'created_at': t.created_at.isoformat()
                    }
                    for t in transcripts
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transcripts: {e}")
            return []
    
    # Analysis operations
    
    def save_meeting_analysis(self, meeting_id: str, analysis_data: Dict[str, Any]) -> str:
        """Save LLM analysis results"""
        try:
            with self.get_session() as session:
                # Check if analysis already exists
                existing = session.query(MeetingAnalysis).filter(
                    MeetingAnalysis.meeting_id == meeting_id
                ).first()
                
                if existing:
                    # Update existing analysis
                    existing.summary = analysis_data.get('meeting_summary', {})
                    existing.action_items = analysis_data.get('action_items', [])
                    existing.key_points = analysis_data.get('key_points', [])
                    existing.code_analysis = analysis_data.get('code_analysis', {})
                    existing.llm_provider = analysis_data.get('provider')
                    existing.token_usage = analysis_data.get('token_usage', {})
                    existing.processing_time = datetime.utcnow()
                    existing.updated_at = datetime.utcnow()
                    analysis_id = existing.id
                else:
                    # Create new analysis
                    analysis = MeetingAnalysis(
                        meeting_id=meeting_id,
                        summary=analysis_data.get('meeting_summary', {}),
                        action_items=analysis_data.get('action_items', []),
                        key_points=analysis_data.get('key_points', []),
                        code_analysis=analysis_data.get('code_analysis', {}),
                        llm_provider=analysis_data.get('provider'),
                        token_usage=analysis_data.get('token_usage', {}),
                        processing_time=datetime.utcnow()
                    )
                    
                    session.add(analysis)
                    session.flush()
                    analysis_id = analysis.id
                
                logger.info(f"Saved analysis for meeting {meeting_id}")
                return analysis_id
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to save analysis: {e}")
            raise
    
    def get_meeting_analysis(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis results for a meeting"""
        try:
            with self.get_session() as session:
                analysis = session.query(MeetingAnalysis).filter(
                    MeetingAnalysis.meeting_id == meeting_id
                ).first()
                
                if not analysis:
                    return None
                
                return {
                    'id': analysis.id,
                    'meeting_id': analysis.meeting_id,
                    'summary': analysis.summary,
                    'action_items': analysis.action_items,
                    'key_points': analysis.key_points,
                    'code_analysis': analysis.code_analysis,
                    'llm_provider': analysis.llm_provider,
                    'processing_time': analysis.processing_time.isoformat() if analysis.processing_time else None,
                    'token_usage': analysis.token_usage,
                    'confidence_score': analysis.confidence_score,
                    'processing_duration': analysis.processing_duration,
                    'created_at': analysis.created_at.isoformat(),
                    'updated_at': analysis.updated_at.isoformat()
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get analysis: {e}")
            return None
    
    # Utility methods
    
    def list_recent_meetings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent meetings"""
        try:
            with self.get_session() as session:
                meetings = session.query(Meeting).order_by(
                    Meeting.created_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'id': m.id,
                        'title': m.title,
                        'status': m.status,
                        'start_time': m.start_time.isoformat() if m.start_time else None,
                        'participants': m.participants,
                        'created_at': m.created_at.isoformat()
                    }
                    for m in meetings
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to list meetings: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_session() as session:
                total_meetings = session.query(Meeting).count()
                completed_meetings = session.query(Meeting).filter(
                    Meeting.status == 'completed'
                ).count()
                total_transcripts = session.query(Transcript).count()
                total_analyses = session.query(MeetingAnalysis).count()
                
                return {
                    'total_meetings': total_meetings,
                    'completed_meetings': completed_meetings,
                    'processing_meetings': total_meetings - completed_meetings,
                    'total_transcripts': total_transcripts,
                    'total_analyses': total_analyses,
                    'database_url': self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create global database service instance"""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
