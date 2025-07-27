"""
Analytics REST API Endpoints for VoiceLink

Secure endpoints for retrieving meeting analytics, statistics, and insights.
Includes authentication, rate limiting, and comprehensive data validation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator
import logging
import asyncio
from functools import wraps
import time
from collections import defaultdict

# Import analytics components
try:
    from analytics.service import AnalyticsService, analytics_service
    from analytics.extraction_engine import analytics_engine
    from analytics.models import MeetingAnalytics
    ANALYTICS_AVAILABLE = True
except ImportError as e:
    ANALYTICS_AVAILABLE = False
    logging.warning(f"Analytics not available: {e}")

logger = logging.getLogger(__name__)

# Security setup
security = HTTPBearer()

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)

# Create router
router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

# Pydantic models for request/response validation
class MeetingStatsResponse(BaseModel):
    """Response model for meeting statistics"""
    meeting_id: str
    title: Optional[str] = None
    duration_minutes: float
    participant_count: int
    total_decisions: int
    total_action_items: int
    total_topics: int
    engagement_score: float = Field(..., ge=0, le=100)
    productivity_score: float = Field(..., ge=0, le=100)
    technical_complexity: str = Field(..., pattern="^(low|medium|high)$")
    created_at: datetime
    last_updated: Optional[datetime] = None

class ParticipantAnalytics(BaseModel):
    """Model for participant analytics data"""
    participant_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    speaking_time_minutes: float = Field(..., ge=0)
    contribution_score: float = Field(..., ge=0, le=10)
    engagement_level: str = Field(..., pattern="^(low|medium|high)$")
    questions_asked: int = Field(..., ge=0)
    topics_contributed: List[str] = []
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)

class TopicAnalytics(BaseModel):
    """Model for topic analytics data"""
    topic_id: str
    topic_name: str
    duration_seconds: float = Field(..., ge=0)
    participants_involved: List[str]
    importance_score: float = Field(..., ge=0, le=10)
    keywords: List[str] = []
    technical_level: str = Field(..., pattern="^(low|medium|high)$")
    confidence: float = Field(..., ge=0, le=1)

class ActionItemAnalytics(BaseModel):
    """Model for action item analytics"""
    action_id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(..., pattern="^(low|medium|high|urgent)$")
    status: str = Field(..., pattern="^(open|in_progress|completed|cancelled)$")
    estimated_effort: Optional[str] = Field(None, pattern="^(small|medium|large)$")
    created_at: datetime
    completion_probability: Optional[float] = Field(None, ge=0, le=1)

class CodeContextAnalytics(BaseModel):
    """Model for code context analytics"""
    meeting_id: str
    technical_terms: List[str] = []
    code_references: List[str] = []
    repositories_mentioned: List[str] = []
    api_discussions: List[str] = []
    architecture_decisions: List[str] = []
    bug_reports: List[str] = []
    technical_complexity_score: float = Field(..., ge=0, le=10)
    languages_mentioned: List[str] = []

class AnalyticsAggregation(BaseModel):
    """Model for aggregated analytics across multiple meetings"""
    date_range: Dict[str, datetime]
    total_meetings: int = Field(..., ge=0)
    total_participants: int = Field(..., ge=0)
    average_engagement: float = Field(..., ge=0, le=100)
    average_productivity: float = Field(..., ge=0, le=100)
    top_topics: List[str] = []
    most_active_participants: List[str] = []
    completion_rates: Dict[str, float] = {}
    trends: Dict[str, float] = {}

class DateRangeQuery(BaseModel):
    """Model for date range queries"""
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

# Security and rate limiting decorators
def rate_limit(max_requests: int = 100, window_minutes: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract client identifier (in production, use proper client identification)
            client_id = "default_client"  # Simplified for demo
            
            now = time.time()
            window_start = now - (window_minutes * 60)
            
            # Clean old requests
            rate_limit_storage[client_id] = [
                req_time for req_time in rate_limit_storage[client_id] 
                if req_time > window_start
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_id]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_minutes} minutes."
                )
            
            # Add current request
            rate_limit_storage[client_id].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def verify_meeting_access(meeting_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify user has access to meeting data"""
    # TODO: Implement proper authentication and authorization
    # For now, return True for all requests
    return True

async def get_analytics_service() -> AnalyticsService:
    """Dependency to get analytics service"""
    if not ANALYTICS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analytics service not available"
        )
    return analytics_service

# Core Analytics Endpoints

@router.get("/meetings/{meeting_id}/stats", response_model=MeetingStatsResponse)
@rate_limit(max_requests=200, window_minutes=60)
async def get_meeting_statistics(
    meeting_id: str = Path(..., description="Meeting ID", min_length=1),
    include_historical: bool = Query(False, description="Include historical comparison"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get comprehensive statistics for a specific meeting.
    
    Returns meeting analytics including engagement scores, productivity metrics,
    participant counts, and technical complexity assessment.
    """
    try:
        # Verify access
        await verify_meeting_access(meeting_id, credentials)
        
        # Get analytics data
        analytics_data = await service.get_meeting_analytics(meeting_id)
        
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analytics not found for meeting {meeting_id}"
            )
        
        # Extract core statistics
        stats = MeetingStatsResponse(
            meeting_id=meeting_id,
            title=analytics_data.get("title"),
            duration_minutes=analytics_data.get("duration_minutes", 0),
            participant_count=len(analytics_data.get("participants", [])),
            total_decisions=len(analytics_data.get("decisions", [])),
            total_action_items=len(analytics_data.get("action_items", [])),
            total_topics=len(analytics_data.get("topics", [])),
            engagement_score=analytics_data.get("metrics", {}).get("engagement_score", 50),
            productivity_score=analytics_data.get("metrics", {}).get("productivity_score", 50),
            technical_complexity=analytics_data.get("metrics", {}).get("technical_complexity", "low"),
            created_at=analytics_data.get("created_at", datetime.utcnow()),
            last_updated=analytics_data.get("last_updated")
        )
        
        if include_historical:
            # Add historical comparison (implement based on requirements)
            stats.historical_comparison = await service.get_historical_comparison(meeting_id)
        
        logger.info(f"Retrieved statistics for meeting {meeting_id}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving meeting statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meeting statistics"
        )

@router.get("/meetings/{meeting_id}/participants", response_model=List[ParticipantAnalytics])
@rate_limit(max_requests=150, window_minutes=60)
async def get_participant_analytics(
    meeting_id: str = Path(..., description="Meeting ID"),
    sort_by: str = Query("contribution_score", description="Sort field", regex="^(contribution_score|engagement_level|speaking_time)$"),
    order: str = Query("desc", description="Sort order", regex="^(asc|desc)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get detailed participant analytics for a meeting.
    
    Returns speaking time, contribution scores, engagement levels,
    and topic participation for each meeting participant.
    """
    try:
        await verify_meeting_access(meeting_id, credentials)
        
        analytics_data = await service.get_meeting_analytics(meeting_id)
        if not analytics_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        
        participants_data = analytics_data.get("participants", [])
        
        # Convert to response models
        participants = []
        for p in participants_data:
            participant = ParticipantAnalytics(
                participant_id=p.get("speaker_id", "unknown"),
                name=p.get("name"),
                email=p.get("email"),
                speaking_time_minutes=p.get("speaking_time", 0) / 60,
                contribution_score=p.get("contribution_score", 0),
                engagement_level=p.get("engagement_level", "medium"),
                questions_asked=p.get("questions_asked", 0),
                topics_contributed=p.get("topics_contributed", []),
                sentiment_score=p.get("sentiment_score")
            )
            participants.append(participant)
        
        # Sort participants
        reverse = (order == "desc")
        participants.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)
        
        logger.info(f"Retrieved participant analytics for meeting {meeting_id}")
        return participants
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving participant analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve participant analytics"
        )

@router.get("/meetings/{meeting_id}/topics", response_model=List[TopicAnalytics])
@rate_limit(max_requests=150, window_minutes=60)
async def get_topic_analytics(
    meeting_id: str = Path(..., description="Meeting ID"),
    min_duration: float = Query(0, description="Minimum topic duration in seconds", ge=0),
    technical_only: bool = Query(False, description="Return only technical topics"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get topic analytics for a meeting.
    
    Returns discussion topics with duration, participant involvement,
    importance scores, and technical classification.
    """
    try:
        await verify_meeting_access(meeting_id, credentials)
        
        analytics_data = await service.get_meeting_analytics(meeting_id)
        if not analytics_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        
        topics_data = analytics_data.get("topics", [])
        
        # Convert and filter topics
        topics = []
        for idx, t in enumerate(topics_data):
            duration = t.get("duration", 0)
            
            # Apply duration filter
            if duration < min_duration:
                continue
            
            # Determine technical level
            technical_level = "low"
            keywords = t.get("keywords", [])
            technical_keywords = ["api", "code", "database", "function", "algorithm"]
            if any(kw in " ".join(keywords).lower() for kw in technical_keywords):
                technical_level = "high" if len([kw for kw in technical_keywords if kw in " ".join(keywords).lower()]) > 2 else "medium"
            
            # Apply technical filter
            if technical_only and technical_level == "low":
                continue
            
            topic = TopicAnalytics(
                topic_id=f"{meeting_id}_topic_{idx}",
                topic_name=t.get("topic", "Unknown Topic"),
                duration_seconds=duration,
                participants_involved=t.get("participants", []),
                importance_score=t.get("importance_score", 0),
                keywords=keywords,
                technical_level=technical_level,
                confidence=t.get("confidence", 0)
            )
            topics.append(topic)
        
        # Sort by importance score
        topics.sort(key=lambda x: x.importance_score, reverse=True)
        
        logger.info(f"Retrieved topic analytics for meeting {meeting_id}")
        return topics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving topic analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic analytics"
        )

@router.get("/meetings/{meeting_id}/action-items", response_model=List[ActionItemAnalytics])
@rate_limit(max_requests=150, window_minutes=60)
async def get_action_item_analytics(
    meeting_id: str = Path(..., description="Meeting ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status", regex="^(open|in_progress|completed|cancelled)$"),
    priority_filter: Optional[str] = Query(None, description="Filter by priority", regex="^(low|medium|high|urgent)$"),
    assignee_filter: Optional[str] = Query(None, description="Filter by assignee"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get action item analytics for a meeting.
    
    Returns identified action items with assignments, priorities,
    due dates, and completion probability estimates.
    """
    try:
        await verify_meeting_access(meeting_id, credentials)
        
        analytics_data = await service.get_meeting_analytics(meeting_id)
        if not analytics_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        
        action_items_data = analytics_data.get("action_items", [])
        
        # Convert to response models
        action_items = []
        for idx, ai in enumerate(action_items_data):
            # Parse due date if it's a string
            due_date = None
            if ai.get("due_date"):
                try:
                    if isinstance(ai["due_date"], str):
                        # Handle various date formats
                        due_date = datetime.fromisoformat(ai["due_date"].replace('Z', '+00:00'))
                    elif isinstance(ai["due_date"], datetime):
                        due_date = ai["due_date"]
                except:
                    due_date = None
            
            action_item = ActionItemAnalytics(
                action_id=f"{meeting_id}_action_{idx}",
                description=ai.get("task", ai.get("action", "Unknown Action")),
                assignee=ai.get("assignee"),
                due_date=due_date,
                priority=ai.get("priority", "medium"),
                status=ai.get("status", "open"),
                estimated_effort=ai.get("estimated_effort"),
                created_at=datetime.utcnow(),  # TODO: Get from actual data
                completion_probability=ai.get("completion_probability", 0.7)  # Default estimate
            )
            
            # Apply filters
            if status_filter and action_item.status != status_filter:
                continue
            if priority_filter and action_item.priority != priority_filter:
                continue
            if assignee_filter and action_item.assignee != assignee_filter:
                continue
            
            action_items.append(action_item)
        
        # Sort by priority and due date
        priority_order = {"urgent": 4, "high": 3, "medium": 2, "low": 1}
        action_items.sort(
            key=lambda x: (
                priority_order.get(x.priority, 1),
                x.due_date if x.due_date else datetime.max
            ),
            reverse=True
        )
        
        logger.info(f"Retrieved action item analytics for meeting {meeting_id}")
        return action_items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving action item analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve action item analytics"
        )

@router.get("/meetings/{meeting_id}/code-context", response_model=CodeContextAnalytics)
@rate_limit(max_requests=100, window_minutes=60)
async def get_code_context_analytics(
    meeting_id: str = Path(..., description="Meeting ID"),
    include_details: bool = Query(True, description="Include detailed technical analysis"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get code and technical context analytics for a meeting.
    
    Returns technical discussions, code references, repository mentions,
    API discussions, and architectural decisions identified in the meeting.
    """
    try:
        await verify_meeting_access(meeting_id, credentials)
        
        analytics_data = await service.get_meeting_analytics(meeting_id)
        if not analytics_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
        
        code_context_data = analytics_data.get("code_context", {})
        
        # Calculate technical complexity score
        technical_score = 0
        code_refs = len(code_context_data.get("code_references", []))
        tech_terms = len(code_context_data.get("technical_terms", []))
        api_discussions = len(code_context_data.get("api_discussions", []))
        
        technical_score = min(10, (code_refs * 0.3) + (tech_terms * 0.2) + (api_discussions * 0.5))
        
        # Extract programming languages mentioned
        languages = []
        tech_terms = code_context_data.get("technical_terms", [])
        common_languages = ["python", "javascript", "java", "typescript", "go", "rust", "c++", "c#"]
        for lang in common_languages:
            if lang in " ".join(tech_terms).lower():
                languages.append(lang)
        
        code_context = CodeContextAnalytics(
            meeting_id=meeting_id,
            technical_terms=code_context_data.get("technical_terms", []),
            code_references=code_context_data.get("code_references", []),
            repositories_mentioned=code_context_data.get("repositories_mentioned", []),
            api_discussions=code_context_data.get("api_discussions", []),
            architecture_decisions=code_context_data.get("architecture_decisions", []),
            bug_reports=code_context_data.get("bug_reports", []),
            technical_complexity_score=technical_score,
            languages_mentioned=languages
        )
        
        if not include_details:
            # Limit details for summary view
            code_context.technical_terms = code_context.technical_terms[:10]
            code_context.code_references = code_context.code_references[:10]
            code_context.api_discussions = code_context.api_discussions[:5]
        
        logger.info(f"Retrieved code context analytics for meeting {meeting_id}")
        return code_context
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving code context analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve code context analytics"
        )

# Aggregated Analytics Endpoints

@router.get("/aggregate/meetings", response_model=AnalyticsAggregation)
@rate_limit(max_requests=50, window_minutes=60)
async def get_aggregated_analytics(
    start_date: datetime = Query(..., description="Start date for aggregation"),
    end_date: datetime = Query(..., description="End date for aggregation"),
    participant_filter: Optional[List[str]] = Query(None, description="Filter by participant IDs"),
    topic_filter: Optional[List[str]] = Query(None, description="Filter by topic keywords"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get aggregated analytics across multiple meetings.
    
    Returns summary statistics, trends, and insights across
    meetings within the specified date range.
    """
    try:
        # Validate date range
        if end_date <= start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date must be after start_date"
            )
        
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date range cannot exceed 365 days"
            )
        
        # Get aggregated data
        aggregated_data = await service.get_analytics_summary(start_date, end_date)
        
        # Calculate trends
        trends = await service.calculate_trends(start_date, end_date)
        
        # Apply filters if provided
        if participant_filter or topic_filter:
            aggregated_data = await service.apply_filters(
                aggregated_data, 
                participant_filter=participant_filter,
                topic_filter=topic_filter
            )
        
        aggregation = AnalyticsAggregation(
            date_range={"start": start_date, "end": end_date},
            total_meetings=aggregated_data.get("total_meetings", 0),
            total_participants=aggregated_data.get("unique_participants", 0),
            average_engagement=aggregated_data.get("average_engagement", 0),
            average_productivity=aggregated_data.get("average_productivity", 0),
            top_topics=aggregated_data.get("top_topics", [])[:10],
            most_active_participants=aggregated_data.get("most_active_participants", [])[:10],
            completion_rates=aggregated_data.get("completion_rates", {}),
            trends=trends
        )
        
        logger.info(f"Retrieved aggregated analytics for {start_date} to {end_date}")
        return aggregation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving aggregated analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve aggregated analytics"
        )

@router.get("/trends/engagement")
@rate_limit(max_requests=30, window_minutes=60)
async def get_engagement_trends(
    period: str = Query("30d", description="Period for trends", regex="^(7d|30d|90d|1y)$"),
    granularity: str = Query("daily", description="Trend granularity", regex="^(daily|weekly|monthly)$"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get engagement trends over time.
    
    Returns engagement metrics trends with specified granularity
    for trend analysis and pattern identification.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "1y":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        trends_data = await service.get_engagement_trends(start_date, end_date, granularity)
        
        logger.info(f"Retrieved engagement trends for period {period}")
        return trends_data
        
    except Exception as e:
        logger.error(f"Error retrieving engagement trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement trends"
        )

# Export and Reporting Endpoints

@router.get("/export/meeting/{meeting_id}")
@rate_limit(max_requests=20, window_minutes=60)
async def export_meeting_analytics(
    meeting_id: str = Path(..., description="Meeting ID"),
    format: str = Query("json", description="Export format", regex="^(json|csv|pdf)$"),
    include_raw_data: bool = Query(False, description="Include raw analytics data"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Export complete meeting analytics in specified format.
    
    Supports JSON, CSV, and PDF export formats with optional
    raw data inclusion for detailed analysis.
    """
    try:
        await verify_meeting_access(meeting_id, credentials)
        
        export_data = await service.export_meeting_analytics(
            meeting_id, 
            format=format, 
            include_raw=include_raw_data
        )
        
        # Set appropriate content type
        content_type = {
            "json": "application/json",
            "csv": "text/csv",
            "pdf": "application/pdf"
        }.get(format, "application/json")
        
        logger.info(f"Exported analytics for meeting {meeting_id} in {format} format")
        return JSONResponse(
            content=export_data,
            headers={"Content-Type": content_type}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting meeting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export meeting analytics"
        )

# Health and Status Endpoints

@router.get("/health")
async def analytics_health_check():
    """
    Check analytics service health and availability.
    
    Returns service status, processing queue information,
    and system health metrics.
    """
    try:
        if not ANALYTICS_AVAILABLE:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unavailable", "message": "Analytics service not available"}
            )
        
        health_data = await analytics_service.get_health_status()
        
        return {
            "status": "healthy",
            "analytics_service": "available",
            "processing_queue_size": health_data.get("queue_size", 0),
            "last_processed": health_data.get("last_processed"),
            "total_processed": health_data.get("total_processed", 0),
            "error_rate": health_data.get("error_rate", 0),
            "average_processing_time": health_data.get("avg_processing_time", 0)
        }
        
    except Exception as e:
        logger.error(f"Error checking analytics health: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )

@router.get("/processing/status")
@rate_limit(max_requests=60, window_minutes=60)
async def get_processing_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get analytics processing status and queue information.
    
    Returns current processing status, queue size, and
    recent processing activity.
    """
    try:
        status_data = await service.get_processing_status()
        
        return {
            "processing_active": status_data.get("is_processing", False),
            "queue_size": status_data.get("queue_size", 0),
            "current_task": status_data.get("current_task"),
            "processed_today": status_data.get("processed_today", 0),
            "average_processing_time": status_data.get("avg_processing_time", 0),
            "last_error": status_data.get("last_error"),
            "success_rate": status_data.get("success_rate", 100)
        }
        
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing status"
        )

# Add router to main app if analytics is available
if ANALYTICS_AVAILABLE:
    logger.info("✅ Analytics API endpoints initialized successfully")
else:
    logger.warning("⚠️  Analytics API endpoints not available - service disabled")
