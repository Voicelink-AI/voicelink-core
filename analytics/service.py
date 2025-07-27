"""
Analytics Service

Service layer that coordinates analytics extraction and database storage.
Automatically processes meetings when they are completed.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_

from analytics.extraction_engine import analytics_engine, AnalyticsType
from analytics.models import (
    MeetingAnalytics, ParticipantAnalyticsDetail, TopicAnalyticsDetail,
    DecisionAnalyticsDetail, ActionItemAnalyticsDetail, CodeContextAnalyticsDetail,
    AnalyticsProcessingLog
)
from persistence.models.database_models import Meeting
from persistence.database_service import get_database_service

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for managing analytics extraction and storage"""
    
    def __init__(self):
        self.db_service = get_database_service()
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
    
    async def start_background_processor(self):
        """Start the background analytics processor"""
        if self.is_processing:
            return
        
        self.is_processing = True
        logger.info("🔄 Starting analytics background processor...")
        
        while self.is_processing:
            try:
                # Check for meetings that need analytics processing
                await self._check_for_unprocessed_meetings()
                
                # Process any queued meetings
                if not self.processing_queue.empty():
                    meeting_id = await self.processing_queue.get()
                    await self._process_meeting_analytics(meeting_id)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in analytics background processor: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def stop_background_processor(self):
        """Stop the background processor"""
        self.is_processing = False
        logger.info("⏹️  Stopped analytics background processor")
    
    async def queue_meeting_for_analytics(self, meeting_id: str):
        """Queue a meeting for analytics processing"""
        try:
            await self.processing_queue.put(meeting_id)
            logger.info(f"📋 Queued meeting {meeting_id} for analytics processing")
        except Exception as e:
            logger.error(f"Error queuing meeting {meeting_id}: {e}")
    
    async def process_meeting_analytics_now(self, meeting_id: str) -> Dict[str, Any]:
        """Process analytics for a meeting immediately"""
        return await self._process_meeting_analytics(meeting_id)
    
    async def get_meeting_analytics(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get stored analytics for a meeting"""
        try:
            with self.db_service.get_session() as session:
                analytics = session.query(MeetingAnalytics).filter(
                    MeetingAnalytics.meeting_id == meeting_id
                ).first()
                
                if not analytics:
                    return None
                
                return {
                    "meeting_id": meeting_id,
                    "participants": analytics.participants_data,
                    "topics": analytics.topics_data,
                    "decisions": analytics.decisions_data,
                    "action_items": analytics.action_items_data,
                    "code_context": analytics.code_context_data,
                    "sentiment": analytics.sentiment_data,
                    "engagement": analytics.engagement_data,
                    "metrics": {
                        "total_participants": analytics.total_participants,
                        "total_topics": analytics.total_topics,
                        "total_decisions": analytics.total_decisions,
                        "total_action_items": analytics.total_action_items,
                        "productivity_score": analytics.productivity_score,
                        "engagement_score": analytics.engagement_score,
                        "technical_complexity": analytics.technical_complexity,
                        "overall_mood": analytics.overall_mood
                    },
                    "processing_info": {
                        "analytics_version": analytics.analytics_version,
                        "processing_duration": analytics.processing_duration,
                        "extraction_timestamp": analytics.extraction_timestamp.isoformat(),
                        "confidence_score": analytics.confidence_score,
                        "completeness_score": analytics.completeness_score
                    }
                }
        except Exception as e:
            logger.error(f"Error retrieving analytics for meeting {meeting_id}: {e}")
            return None
    
    async def get_analytics_summary(self, start_date: Optional[datetime] = None, 
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get analytics summary across multiple meetings"""
        try:
            with self.db_service.get_session() as session:
                query = session.query(MeetingAnalytics)
                
                if start_date:
                    query = query.filter(MeetingAnalytics.created_at >= start_date)
                if end_date:
                    query = query.filter(MeetingAnalytics.created_at <= end_date)
                
                analytics_records = query.all()
                
                if not analytics_records:
                    return {"message": "No analytics data found for the specified period"}
                
                # Aggregate metrics
                total_meetings = len(analytics_records)
                total_participants = sum(a.total_participants for a in analytics_records)
                total_decisions = sum(a.total_decisions for a in analytics_records)
                total_action_items = sum(a.total_action_items for a in analytics_records)
                
                avg_productivity = sum(a.productivity_score for a in analytics_records) / total_meetings
                avg_engagement = sum(a.engagement_score for a in analytics_records) / total_meetings
                
                # Mood distribution
                mood_distribution = {}
                for record in analytics_records:
                    mood = record.overall_mood
                    mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
                
                # Technical complexity distribution
                complexity_distribution = {}
                for record in analytics_records:
                    complexity = record.technical_complexity
                    complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
                
                return {
                    "period_summary": {
                        "total_meetings_analyzed": total_meetings,
                        "total_participants": total_participants,
                        "total_decisions_made": total_decisions,
                        "total_action_items_created": total_action_items,
                        "average_productivity_score": round(avg_productivity, 2),
                        "average_engagement_score": round(avg_engagement, 2)
                    },
                    "distributions": {
                        "mood_distribution": mood_distribution,
                        "technical_complexity_distribution": complexity_distribution
                    },
                    "trends": await self._calculate_trends(analytics_records)
                }
        except Exception as e:
            logger.error(f"Error generating analytics summary: {e}")
            return {"error": f"Failed to generate analytics summary: {e}"}
    
    async def _check_for_unprocessed_meetings(self):
        """Check for meetings that need analytics processing"""
        try:
            with self.db_service.get_session() as session:
                # Find completed meetings without analytics
                unprocessed_meetings = session.query(Meeting).filter(
                    and_(
                        Meeting.status == 'completed',
                        ~Meeting.meeting_id.in_(
                            session.query(MeetingAnalytics.meeting_id)
                        )
                    )
                ).limit(5).all()  # Process max 5 at a time
                
                for meeting in unprocessed_meetings:
                    await self.queue_meeting_for_analytics(meeting.meeting_id)
                    
        except Exception as e:
            logger.error(f"Error checking for unprocessed meetings: {e}")
    
    async def _process_meeting_analytics(self, meeting_id: str) -> Dict[str, Any]:
        """Process analytics for a specific meeting"""
        processing_start = datetime.utcnow()
        log_entry = None
        
        try:
            logger.info(f"🔍 Starting analytics processing for meeting {meeting_id}")
            
            # Create processing log entry
            with self.db_service.get_session() as session:
                log_entry = AnalyticsProcessingLog(
                    meeting_id=meeting_id,
                    processing_start=processing_start,
                    status='processing'
                )
                session.add(log_entry)
                session.commit()
                log_id = log_entry.id
            
            # Get meeting data
            meeting_data = await self._get_meeting_data(meeting_id)
            if not meeting_data:
                raise Exception(f"Meeting {meeting_id} not found or incomplete")
            
            # Extract analytics
            analytics_results = await analytics_engine.extract_all_analytics(meeting_data)
            
            # Store analytics in database
            analytics_id = await self._store_analytics(meeting_id, analytics_results, processing_start)
            
            # Update processing log
            processing_end = datetime.utcnow()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            with self.db_service.get_session() as session:
                log_entry = session.query(AnalyticsProcessingLog).filter(
                    AnalyticsProcessingLog.id == log_id
                ).first()
                
                if log_entry:
                    log_entry.status = 'completed'
                    log_entry.processing_end = processing_end
                    log_entry.processing_duration = processing_duration
                    log_entry.analytics_extracted = {
                        "participants": len(analytics_results.get("participants", [])),
                        "topics": len(analytics_results.get("topics", [])),
                        "decisions": len(analytics_results.get("decisions", [])),
                        "action_items": len(analytics_results.get("action_items", []))
                    }
                    session.commit()
            
            logger.info(f"✅ Analytics processing completed for meeting {meeting_id} in {processing_duration:.2f}s")
            
            return {
                "status": "success",
                "meeting_id": meeting_id,
                "analytics_id": analytics_id,
                "processing_duration": processing_duration,
                "analytics_summary": analytics_results.get("aggregated_metrics", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing analytics for meeting {meeting_id}: {e}")
            
            # Update processing log with error
            if log_entry:
                processing_end = datetime.utcnow()
                processing_duration = (processing_end - processing_start).total_seconds()
                
                with self.db_service.get_session() as session:
                    log_entry = session.query(AnalyticsProcessingLog).filter(
                        AnalyticsProcessingLog.id == log_entry.id
                    ).first()
                    
                    if log_entry:
                        log_entry.status = 'failed'
                        log_entry.processing_end = processing_end
                        log_entry.processing_duration = processing_duration
                        log_entry.error_details = str(e)
                        session.commit()
            
            return {
                "status": "error",
                "meeting_id": meeting_id,
                "error": str(e)
            }
    
    async def _get_meeting_data(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """Get meeting data from database"""
        try:
            with self.db_service.get_session() as session:
                meeting = session.query(Meeting).filter(
                    Meeting.meeting_id == meeting_id
                ).first()
                
                if not meeting:
                    return None
                
                # Get transcript data (assuming it's stored in the meeting record)
                transcripts = meeting.transcript if meeting.transcript else []
                
                return {
                    "meeting_id": meeting_id,
                    "title": meeting.title,
                    "participants": meeting.participants if meeting.participants else [],
                    "transcripts": transcripts,
                    "speaker_segments": [],  # This would come from audio processing
                    "voice_segments": [],    # This would come from audio processing
                    "audio_info": {
                        "duration_seconds": meeting.audio_duration if meeting.audio_duration else 0
                    }
                }
        except Exception as e:
            logger.error(f"Error getting meeting data for {meeting_id}: {e}")
            return None
    
    async def _store_analytics(self, meeting_id: str, analytics_results: Dict[str, Any], 
                              processing_start: datetime) -> str:
        """Store analytics results in database"""
        try:
            with self.db_service.get_session() as session:
                # Create main analytics record
                processing_duration = (datetime.utcnow() - processing_start).total_seconds()
                aggregated = analytics_results.get("aggregated_metrics", {})
                
                analytics_record = MeetingAnalytics(
                    meeting_id=meeting_id,
                    participants_data=analytics_results.get("participants"),
                    total_participants=aggregated.get("total_participants", 0),
                    topics_data=analytics_results.get("topics"),
                    total_topics=aggregated.get("total_topics", 0),
                    decisions_data=analytics_results.get("decisions"),
                    total_decisions=aggregated.get("total_decisions", 0),
                    action_items_data=analytics_results.get("action_items"),
                    total_action_items=aggregated.get("total_action_items", 0),
                    code_context_data=analytics_results.get("code_context"),
                    technical_complexity=aggregated.get("technical_complexity", "low"),
                    sentiment_data=analytics_results.get("sentiment"),
                    overall_mood=analytics_results.get("sentiment", {}).get("mood", "neutral"),
                    engagement_data=analytics_results.get("engagement"),
                    engagement_score=aggregated.get("engagement_score", 50.0),
                    productivity_score=aggregated.get("meeting_productivity_score", 50.0),
                    processing_duration=processing_duration,
                    confidence_score=0.8,  # Could be calculated from individual confidences
                    completeness_score=0.8  # Could be calculated based on available data
                )
                
                session.add(analytics_record)
                session.commit()
                
                logger.info(f"📊 Stored analytics for meeting {meeting_id}")
                return analytics_record.id
                
        except Exception as e:
            logger.error(f"Error storing analytics for meeting {meeting_id}: {e}")
            raise
    
    async def _calculate_trends(self, analytics_records: List[MeetingAnalytics]) -> Dict[str, Any]:
        """Calculate trends from analytics records"""
        try:
            if len(analytics_records) < 2:
                return {"message": "Insufficient data for trend analysis"}
            
            # Sort by creation date
            sorted_records = sorted(analytics_records, key=lambda x: x.created_at)
            
            # Calculate trends for key metrics
            productivity_scores = [r.productivity_score for r in sorted_records]
            engagement_scores = [r.engagement_score for r in sorted_records]
            
            def calculate_trend(values):
                if len(values) < 2:
                    return 0
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                return round(avg_second - avg_first, 2)
            
            return {
                "productivity_trend": calculate_trend(productivity_scores),
                "engagement_trend": calculate_trend(engagement_scores),
                "total_meetings_in_period": len(analytics_records),
                "trend_analysis": {
                    "improving": calculate_trend(productivity_scores) > 5,
                    "stable": abs(calculate_trend(productivity_scores)) <= 5,
                    "declining": calculate_trend(productivity_scores) < -5
                }
            }
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {"error": "Failed to calculate trends"}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get analytics service health status"""
        try:
            return {
                "status": "healthy",
                "queue_size": self.processing_queue.qsize(),
                "is_processing": self.is_processing,
                "last_processed": getattr(self, '_last_processed_time', None),
                "total_processed": getattr(self, '_total_processed', 0),
                "error_rate": getattr(self, '_error_rate', 0),
                "avg_processing_time": getattr(self, '_avg_processing_time', 0)
            }
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        try:
            return {
                "is_processing": self.is_processing,
                "queue_size": self.processing_queue.qsize(),
                "current_task": getattr(self, '_current_task', None),
                "processed_today": getattr(self, '_processed_today', 0),
                "avg_processing_time": getattr(self, '_avg_processing_time', 0),
                "last_error": getattr(self, '_last_error', None),
                "success_rate": getattr(self, '_success_rate', 100)
            }
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {}
    
    async def calculate_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate analytics trends over time"""
        try:
            with self.db_service.get_session() as session:
                # Get meetings in date range
                meetings = session.query(MeetingAnalytics).filter(
                    and_(
                        MeetingAnalytics.created_at >= start_date,
                        MeetingAnalytics.created_at <= end_date
                    )
                ).order_by(MeetingAnalytics.created_at).all()
                
                if len(meetings) < 2:
                    return {"engagement_trend": 0, "productivity_trend": 0}
                
                # Calculate trends (simple linear trend)
                mid_point = len(meetings) // 2
                first_half = meetings[:mid_point]
                second_half = meetings[mid_point:]
                
                avg_engagement_first = sum(m.engagement_score or 0 for m in first_half) / len(first_half)
                avg_engagement_second = sum(m.engagement_score or 0 for m in second_half) / len(second_half)
                
                avg_productivity_first = sum(m.productivity_score or 0 for m in first_half) / len(first_half)
                avg_productivity_second = sum(m.productivity_score or 0 for m in second_half) / len(second_half)
                
                engagement_trend = avg_engagement_second - avg_engagement_first
                productivity_trend = avg_productivity_second - avg_productivity_first
                
                return {
                    "engagement_trend": round(engagement_trend, 2),
                    "productivity_trend": round(productivity_trend, 2)
                }
                
        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {"engagement_trend": 0, "productivity_trend": 0}
    
    async def apply_filters(self, data: Dict[str, Any], participant_filter: Optional[List[str]] = None,
                          topic_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Apply filters to aggregated data"""
        try:
            filtered_data = data.copy()
            
            # Apply participant filter
            if participant_filter and "participants" in filtered_data:
                if isinstance(filtered_data["participants"], list):
                    filtered_data["participants"] = [
                        p for p in filtered_data["participants"]
                        if any(name.lower() in str(p).lower() for name in participant_filter)
                    ]
            
            # Apply topic filter
            if topic_filter and "topics" in filtered_data:
                if isinstance(filtered_data["topics"], list):
                    filtered_data["topics"] = [
                        t for t in filtered_data["topics"]
                        if any(topic.lower() in str(t).lower() for topic in topic_filter)
                    ]
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return data
    
    async def get_engagement_trends(self, start_date: datetime, end_date: datetime, 
                                  granularity: str = "daily") -> Dict[str, Any]:
        """Get engagement trends with specified granularity"""
        try:
            with self.db_service.get_session() as session:
                meetings = session.query(MeetingAnalytics).filter(
                    and_(
                        MeetingAnalytics.created_at >= start_date,
                        MeetingAnalytics.created_at <= end_date
                    )
                ).order_by(MeetingAnalytics.created_at).all()
                
                if not meetings:
                    return {
                        "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                        "granularity": granularity,
                        "engagement_trend": 0,
                        "data_points": []
                    }
                
                # Calculate basic trend
                trends = await self.calculate_trends(start_date, end_date)
                
                # TODO: Implement proper time-series data points based on granularity
                data_points = []
                for meeting in meetings:
                    data_points.append({
                        "date": meeting.created_at.isoformat(),
                        "engagement_score": meeting.engagement_score,
                        "meeting_id": meeting.meeting_id
                    })
                
                return {
                    "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                    "granularity": granularity,
                    "engagement_trend": trends.get("engagement_trend", 0),
                    "data_points": data_points[:50]  # Limit to 50 points
                }
                
        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            return {
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "granularity": granularity,
                "engagement_trend": 0,
                "data_points": []
            }
    
    async def export_meeting_analytics(self, meeting_id: str, format: str = "json", 
                                     include_raw: bool = False) -> Dict[str, Any]:
        """Export meeting analytics in specified format"""
        try:
            analytics_data = await self.get_meeting_analytics(meeting_id)
            
            if not analytics_data:
                return {"error": "Meeting analytics not found"}
            
            export_data = {
                "export_info": {
                    "meeting_id": meeting_id,
                    "format": format,
                    "exported_at": datetime.utcnow().isoformat(),
                    "include_raw_data": include_raw
                },
                "analytics": analytics_data
            }
            
            if include_raw:
                # Include raw processing data if requested
                with self.db_service.get_session() as session:
                    raw_data = session.query(AnalyticsProcessingLog).filter(
                        AnalyticsProcessingLog.meeting_id == meeting_id
                    ).first()
                    
                    if raw_data:
                        export_data["raw_processing_data"] = {
                            "processing_duration": raw_data.processing_duration,
                            "analytics_extracted": raw_data.analytics_extracted,
                            "status": raw_data.status
                        }
            
            if format == "csv":
                # TODO: Implement CSV conversion
                export_data["format_note"] = "CSV conversion available upon request"
            elif format == "pdf":
                # TODO: Implement PDF generation
                export_data["format_note"] = "PDF generation available upon request"
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting analytics for meeting {meeting_id}: {e}")
            return {"error": str(e)}
    
    async def get_participant_analytics(self, meeting_id: str, participant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get participant analytics for a meeting"""
        try:
            analytics_data = await self.get_meeting_analytics(meeting_id)
            
            if not analytics_data:
                return {"error": "Meeting analytics not found"}
            
            participants = analytics_data.get("participants", [])
            
            if participant_id:
                # Filter for specific participant
                participant_data = None
                for p in participants:
                    if p.get("speaker_id") == participant_id or p.get("name") == participant_id:
                        participant_data = p
                        break
                
                if not participant_data:
                    return {"error": f"Participant {participant_id} not found in meeting {meeting_id}"}
                
                return {
                    "meeting_id": meeting_id,
                    "participant": participant_data
                }
            else:
                return {
                    "meeting_id": meeting_id,
                    "participants": participants,
                    "participant_count": len(participants)
                }
                
        except Exception as e:
            logger.error(f"Error getting participant analytics: {e}")
            return {"error": str(e)}
    
    async def get_topic_analytics(self, meeting_id: str, topic_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get topic analytics for a meeting"""
        try:
            analytics_data = await self.get_meeting_analytics(meeting_id)
            
            if not analytics_data:
                return {"error": "Meeting analytics not found"}
            
            topics = analytics_data.get("topics", [])
            
            if topic_filter:
                # Filter topics by keyword
                filtered_topics = [
                    t for t in topics
                    if topic_filter.lower() in str(t).lower()
                ]
                topics = filtered_topics
            
            return {
                "meeting_id": meeting_id,
                "topics": topics,
                "topic_count": len(topics)
            }
            
        except Exception as e:
            logger.error(f"Error getting topic analytics: {e}")
            return {"error": str(e)}
    
    async def get_action_items_analytics(self, meeting_id: str, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get action items analytics for a meeting"""
        try:
            analytics_data = await self.get_meeting_analytics(meeting_id)
            
            if not analytics_data:
                return {"error": "Meeting analytics not found"}
            
            action_items = analytics_data.get("action_items", [])
            
            if status_filter:
                # Filter by status if provided
                filtered_items = [
                    item for item in action_items
                    if item.get("status", "").lower() == status_filter.lower()
                ]
                action_items = filtered_items
            
            return {
                "meeting_id": meeting_id,
                "action_items": action_items,
                "action_item_count": len(action_items)
            }
            
        except Exception as e:
            logger.error(f"Error getting action items analytics: {e}")
            return {"error": str(e)}
    
    async def get_code_context_analytics(self, meeting_id: str) -> Dict[str, Any]:
        """Get code context analytics for a meeting"""
        try:
            analytics_data = await self.get_meeting_analytics(meeting_id)
            
            if not analytics_data:
                return {"error": "Meeting analytics not found"}
            
            code_context = analytics_data.get("code_context", {})
            
            return {
                "meeting_id": meeting_id,
                "code_context": code_context,
                "has_technical_content": bool(code_context)
            }
            
        except Exception as e:
            logger.error(f"Error getting code context analytics: {e}")
            return {"error": str(e)}

# Global analytics service instance
analytics_service = AnalyticsService()

# Convenience functions
async def process_meeting_analytics(meeting_id: str) -> Dict[str, Any]:
    """Process analytics for a meeting"""
    return await analytics_service.process_meeting_analytics_now(meeting_id)

async def get_meeting_analytics(meeting_id: str) -> Optional[Dict[str, Any]]:
    """Get analytics for a meeting"""
    return await analytics_service.get_meeting_analytics(meeting_id)

async def get_analytics_summary(start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
    """Get analytics summary"""
    return await analytics_service.get_analytics_summary(start_date, end_date)

async def start_analytics_processor():
    """Start the background analytics processor"""
    await analytics_service.start_background_processor()

async def stop_analytics_processor():
    """Stop the background analytics processor"""
    await analytics_service.stop_background_processor()
