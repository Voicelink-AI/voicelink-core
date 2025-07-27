"""
Analytics Database Models

Extended database models for storing analytics data extracted from meetings.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Use the existing base from the main models
from persistence.models.database_models import Base

class MeetingAnalytics(Base):
    """Comprehensive analytics data for each meeting"""
    __tablename__ = 'meeting_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    
    # Participant analytics
    participants_data = Column(JSON)  # List of ParticipantAnalytics
    total_participants = Column(Integer, default=0)
    
    # Topic analytics  
    topics_data = Column(JSON)  # List of TopicAnalytics
    total_topics = Column(Integer, default=0)
    
    # Decision analytics
    decisions_data = Column(JSON)  # List of DecisionAnalytics
    total_decisions = Column(Integer, default=0)
    
    # Action item analytics
    action_items_data = Column(JSON)  # List of ActionItemAnalytics
    total_action_items = Column(Integer, default=0)
    
    # Code context analytics
    code_context_data = Column(JSON)  # CodeContextAnalytics
    technical_complexity = Column(String, default='low')  # low, medium, high
    
    # Sentiment analytics
    sentiment_data = Column(JSON)  # Overall sentiment analysis
    overall_mood = Column(String, default='neutral')  # positive, negative, neutral
    
    # Engagement analytics
    engagement_data = Column(JSON)  # Engagement metrics
    engagement_score = Column(Float, default=50.0)  # 0-100
    
    # Aggregated metrics
    productivity_score = Column(Float, default=50.0)  # 0-100
    meeting_effectiveness = Column(String, default='medium')  # low, medium, high
    
    # Processing metadata
    analytics_version = Column(String, default='1.0')
    processing_duration = Column(Float)  # seconds
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Quality metrics
    confidence_score = Column(Float, default=0.8)  # 0-1
    completeness_score = Column(Float, default=0.8)  # 0-1
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ParticipantAnalyticsDetail(Base):
    """Detailed participant analytics for individual participants"""
    __tablename__ = 'participant_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    analytics_id = Column(String, ForeignKey('meeting_analytics.id'), nullable=False)
    
    # Participant identification
    speaker_id = Column(String, nullable=False)
    participant_name = Column(String)
    participant_email = Column(String)
    
    # Speaking metrics
    speaking_time = Column(Float, default=0.0)  # seconds
    speaking_percentage = Column(Float, default=0.0)  # percentage of total time
    word_count = Column(Integer, default=0)
    turn_count = Column(Integer, default=0)
    average_turn_length = Column(Float, default=0.0)
    
    # Engagement metrics
    contribution_score = Column(Float, default=0.0)  # 0-10
    engagement_level = Column(String, default='medium')  # low, medium, high
    questions_asked = Column(Integer, default=0)
    interruptions = Column(Integer, default=0)
    
    # Topic contributions
    topics_contributed = Column(JSON)  # List of topic names
    technical_contributions = Column(JSON)  # List of technical terms/topics
    
    # Sentiment for this participant
    sentiment_positive = Column(Float, default=0.33)
    sentiment_negative = Column(Float, default=0.33)
    sentiment_neutral = Column(Float, default=0.34)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class TopicAnalyticsDetail(Base):
    """Detailed analytics for each topic discussed"""
    __tablename__ = 'topic_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    analytics_id = Column(String, ForeignKey('meeting_analytics.id'), nullable=False)
    
    # Topic information
    topic_name = Column(String, nullable=False)
    topic_category = Column(String)  # e.g., "technical", "business", "planning"
    
    # Discussion metrics
    discussion_duration = Column(Float, default=0.0)  # seconds
    participants_involved = Column(JSON)  # List of speaker IDs
    confidence_score = Column(Float, default=0.0)  # 0-1
    importance_score = Column(Float, default=0.0)  # calculated importance
    
    # Content analysis
    keywords_found = Column(JSON)  # List of relevant keywords
    key_phrases = Column(JSON)  # Important phrases about this topic
    sentiment_about_topic = Column(String, default='neutral')
    
    # Outcomes
    decisions_made = Column(JSON)  # Related decisions
    action_items_generated = Column(JSON)  # Related action items
    
    created_at = Column(DateTime, default=datetime.utcnow)

class DecisionAnalyticsDetail(Base):
    """Detailed analytics for decisions made during meetings"""
    __tablename__ = 'decision_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    analytics_id = Column(String, ForeignKey('meeting_analytics.id'), nullable=False)
    
    # Decision information
    decision_text = Column(Text, nullable=False)
    decision_category = Column(String)  # technical, business, process, etc.
    
    # Context and timing
    timestamp_in_meeting = Column(Float, default=0.0)  # seconds from start
    context_summary = Column(Text)
    leading_discussion = Column(Text)  # What led to this decision
    
    # Participants and consensus
    decision_maker = Column(String)  # Primary decision maker
    participants_involved = Column(JSON)  # List of speaker IDs
    consensus_level = Column(String, default='medium')  # low, medium, high
    
    # Priority and impact
    priority_level = Column(String, default='medium')  # low, medium, high, critical
    impact_assessment = Column(String, default='medium')  # low, medium, high
    confidence_score = Column(Float, default=0.5)  # 0-1
    
    # Implementation tracking
    related_action_items = Column(JSON)  # List of action item IDs
    implementation_status = Column(String, default='pending')  # pending, in_progress, completed
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ActionItemAnalyticsDetail(Base):
    """Detailed analytics for action items extracted from meetings"""
    __tablename__ = 'action_item_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    analytics_id = Column(String, ForeignKey('meeting_analytics.id'), nullable=False)
    
    # Action item information
    task_description = Column(Text, nullable=False)
    task_category = Column(String)  # development, review, communication, etc.
    
    # Assignment and ownership
    assignee_speaker_id = Column(String)
    assignee_name = Column(String)
    assigner_speaker_id = Column(String)
    
    # Timeline and priority
    due_date_mentioned = Column(String)  # as mentioned in meeting
    due_date_parsed = Column(DateTime)  # parsed date if possible
    priority_level = Column(String, default='medium')  # low, medium, high, urgent
    estimated_effort = Column(String)  # small, medium, large
    
    # Context
    context_summary = Column(Text)
    related_topic = Column(String)
    related_decisions = Column(JSON)  # List of related decision IDs
    
    # Status tracking
    status = Column(String, default='open')  # open, in_progress, completed, cancelled
    confidence_score = Column(Float, default=0.7)  # confidence in extraction
    
    # Dependencies and blockers
    dependencies = Column(JSON)  # List of other action items this depends on
    potential_blockers = Column(JSON)  # Identified potential issues
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CodeContextAnalyticsDetail(Base):
    """Detailed analytics for code and technical context discussed"""
    __tablename__ = 'code_context_analytics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    analytics_id = Column(String, ForeignKey('meeting_analytics.id'), nullable=False)
    
    # Code references
    code_references = Column(JSON)  # Functions, methods, classes mentioned
    file_references = Column(JSON)  # Files or paths mentioned
    repository_references = Column(JSON)  # Repos or projects mentioned
    
    # Technical discussions
    technical_terms = Column(JSON)  # Technical terminology used
    api_discussions = Column(JSON)  # API endpoints, integrations discussed
    architecture_topics = Column(JSON)  # Architecture decisions and patterns
    
    # Issues and improvements
    bug_reports = Column(JSON)  # Bugs or issues mentioned
    performance_topics = Column(JSON)  # Performance-related discussions
    security_topics = Column(JSON)  # Security considerations
    
    # Development process
    development_practices = Column(JSON)  # Practices, methodologies discussed
    tool_mentions = Column(JSON)  # Development tools mentioned
    deployment_topics = Column(JSON)  # Deployment and infrastructure
    
    # Complexity assessment
    technical_complexity_score = Column(Float, default=0.0)  # 0-10
    code_impact_assessment = Column(String, default='low')  # low, medium, high
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalyticsProcessingLog(Base):
    """Log of analytics processing attempts and results"""
    __tablename__ = 'analytics_processing_log'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    
    # Processing details
    processing_start = Column(DateTime, default=datetime.utcnow)
    processing_end = Column(DateTime)
    processing_duration = Column(Float)  # seconds
    
    # Status and results
    status = Column(String, default='pending')  # pending, processing, completed, failed
    analytics_extracted = Column(JSON)  # Summary of what was extracted
    error_details = Column(Text)  # Error information if failed
    
    # Performance metrics
    transcripts_processed = Column(Integer, default=0)
    audio_duration_processed = Column(Float, default=0.0)
    extraction_efficiency = Column(Float)  # analytics per second
    
    # Quality metrics
    extraction_confidence = Column(Float, default=0.0)  # overall confidence
    completeness_score = Column(Float, default=0.0)  # how complete the extraction was
    
    # Version and configuration
    engine_version = Column(String, default='1.0')
    extraction_config = Column(JSON)  # Configuration used for extraction
    
    created_at = Column(DateTime, default=datetime.utcnow)

# Relationships (add to existing Meeting model if needed)
# meeting.analytics = relationship("MeetingAnalytics", back_populates="meeting", uselist=False)
# meeting.participant_analytics = relationship("ParticipantAnalyticsDetail", back_populates="meeting")
# meeting.topic_analytics = relationship("TopicAnalyticsDetail", back_populates="meeting")
# meeting.decision_analytics = relationship("DecisionAnalyticsDetail", back_populates="meeting")
# meeting.action_item_analytics = relationship("ActionItemAnalyticsDetail", back_populates="meeting")
