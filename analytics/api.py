"""
Analytics API Endpoints

FastAPI routes for analytics functionality including extraction, retrieval, and reporting.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from analytics.service import analytics_service, process_meeting_analytics, get_meeting_analytics, get_analytics_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.post("/meetings/{meeting_id}/process")
async def trigger_meeting_analytics(meeting_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger analytics processing for a specific meeting"""
    try:
        # Add to background processing queue
        await analytics_service.queue_meeting_for_analytics(meeting_id)
        
        return {
            "status": "queued",
            "meeting_id": meeting_id,
            "message": "Analytics processing has been queued for this meeting"
        }
    except Exception as e:
        logger.error(f"Error triggering analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to trigger analytics: {e}"})

@router.post("/meetings/{meeting_id}/process-now")
async def process_meeting_analytics_immediately(meeting_id: str) -> Dict[str, Any]:
    """Process analytics for a meeting immediately (synchronous)"""
    try:
        result = await process_meeting_analytics(meeting_id)
        return result
    except Exception as e:
        logger.error(f"Error processing analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to process analytics: {e}"})

@router.get("/meetings/{meeting_id}")
async def get_meeting_analytics_endpoint(meeting_id: str) -> Dict[str, Any]:
    """Get analytics data for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve analytics: {e}"})

@router.get("/meetings/{meeting_id}/participants")
async def get_meeting_participant_analytics(meeting_id: str) -> Dict[str, Any]:
    """Get participant analytics for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        return {
            "meeting_id": meeting_id,
            "participants": analytics.get("participants", []),
            "participant_summary": {
                "total_participants": len(analytics.get("participants", [])),
                "most_active": _find_most_active_participant(analytics.get("participants", [])),
                "engagement_distribution": _calculate_engagement_distribution(analytics.get("participants", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving participant analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve participant analytics: {e}"})

@router.get("/meetings/{meeting_id}/topics")
async def get_meeting_topic_analytics(meeting_id: str) -> Dict[str, Any]:
    """Get topic analytics for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        topics = analytics.get("topics", [])
        
        return {
            "meeting_id": meeting_id,
            "topics": topics,
            "topic_summary": {
                "total_topics": len(topics),
                "most_discussed": _find_most_discussed_topic(topics),
                "topic_categories": _categorize_topics(topics),
                "discussion_time_distribution": _calculate_topic_time_distribution(topics)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving topic analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve topic analytics: {e}"})

@router.get("/meetings/{meeting_id}/decisions")
async def get_meeting_decision_analytics(meeting_id: str) -> Dict[str, Any]:
    """Get decision analytics for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        decisions = analytics.get("decisions", [])
        
        return {
            "meeting_id": meeting_id,
            "decisions": decisions,
            "decision_summary": {
                "total_decisions": len(decisions),
                "high_priority_decisions": len([d for d in decisions if d.get("priority") in ["high", "critical"]]),
                "decision_confidence": _calculate_average_confidence(decisions),
                "priority_distribution": _calculate_priority_distribution(decisions)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving decision analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve decision analytics: {e}"})

@router.get("/meetings/{meeting_id}/action-items")
async def get_meeting_action_item_analytics(meeting_id: str) -> Dict[str, Any]:
    """Get action item analytics for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        action_items = analytics.get("action_items", [])
        
        return {
            "meeting_id": meeting_id,
            "action_items": action_items,
            "action_item_summary": {
                "total_action_items": len(action_items),
                "assigned_items": len([ai for ai in action_items if ai.get("assignee")]),
                "unassigned_items": len([ai for ai in action_items if not ai.get("assignee")]),
                "priority_distribution": _calculate_priority_distribution(action_items),
                "assignee_distribution": _calculate_assignee_distribution(action_items)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving action item analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve action item analytics: {e}"})

@router.get("/meetings/{meeting_id}/code-context")
async def get_meeting_code_context_analytics(meeting_id: str) -> Dict[str, Any]:
    """Get code context analytics for a specific meeting"""
    try:
        analytics = await get_meeting_analytics(meeting_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail={"message": "Analytics not found for this meeting"})
        
        code_context = analytics.get("code_context", {})
        
        return {
            "meeting_id": meeting_id,
            "code_context": code_context,
            "technical_summary": {
                "technical_complexity": analytics.get("metrics", {}).get("technical_complexity", "low"),
                "code_references_count": len(code_context.get("code_references", [])),
                "repositories_mentioned": len(code_context.get("repositories_mentioned", [])),
                "technical_terms_count": len(code_context.get("technical_terms", [])),
                "api_discussions_count": len(code_context.get("api_discussions", []))
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving code context analytics for meeting {meeting_id}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to retrieve code context analytics: {e}"})

@router.get("/overview")
async def get_analytics_overview(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: Optional[str] = Query("30d", description="Period (7d, 30d, 90d, 1y)")
) -> Dict[str, Any]:
    """Get analytics overview for a date range"""
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Handle period parameter if dates not provided
        if not start_dt and not end_dt:
            end_dt = datetime.utcnow()
            if period == "7d":
                start_dt = end_dt - timedelta(days=7)
            elif period == "30d":
                start_dt = end_dt - timedelta(days=30)
            elif period == "90d":
                start_dt = end_dt - timedelta(days=90)
            elif period == "1y":
                start_dt = end_dt - timedelta(days=365)
            else:
                start_dt = end_dt - timedelta(days=30)  # Default to 30 days
        
        summary = await get_analytics_summary(start_dt, end_dt)
        
        return {
            "period": {
                "start_date": start_dt.isoformat() if start_dt else None,
                "end_date": end_dt.isoformat() if end_dt else None,
                "period_name": period
            },
            "analytics_summary": summary
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": f"Invalid date format: {e}"})
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to generate overview: {e}"})

@router.get("/trends")
async def get_analytics_trends(
    metric: str = Query("productivity", description="Metric to analyze (productivity, engagement, decisions)"),
    period: str = Query("30d", description="Period for trend analysis")
) -> Dict[str, Any]:
    """Get analytics trends for specific metrics"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        summary = await get_analytics_summary(start_date, end_date)
        trends = summary.get("trends", {})
        
        # Extract specific metric trend
        if metric == "productivity":
            trend_value = trends.get("productivity_trend", 0)
        elif metric == "engagement":
            trend_value = trends.get("engagement_trend", 0)
        else:
            trend_value = 0
        
        return {
            "metric": metric,
            "period": period,
            "trend_value": trend_value,
            "trend_direction": "improving" if trend_value > 2 else "declining" if trend_value < -2 else "stable",
            "period_data": summary,
            "interpretation": _interpret_trend(metric, trend_value)
        }
    except Exception as e:
        logger.error(f"Error generating trends for {metric}: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to generate trends: {e}"})

@router.get("/export")
async def export_analytics_data(
    format: str = Query("json", description="Export format (json, csv)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """Export analytics data in specified format"""
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        summary = await get_analytics_summary(start_dt, end_dt)
        
        if format.lower() == "json":
            return {
                "export_format": "json",
                "export_timestamp": datetime.utcnow().isoformat(),
                "data": summary
            }
        elif format.lower() == "csv":
            # For CSV, we'd need to implement CSV conversion
            # For now, return a structured format suitable for CSV conversion
            return {
                "export_format": "csv",
                "export_timestamp": datetime.utcnow().isoformat(),
                "message": "CSV export format - implement CSV conversion as needed",
                "structured_data": summary
            }
        else:
            raise HTTPException(status_code=400, detail={"message": f"Unsupported export format: {format}"})
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"message": f"Invalid date format: {e}"})
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to export data: {e}"})

@router.get("/processing-status")
async def get_processing_status() -> Dict[str, Any]:
    """Get analytics processing status"""
    try:
        return {
            "processor_running": analytics_service.is_processing,
            "queue_size": analytics_service.processing_queue.qsize(),
            "status": "active" if analytics_service.is_processing else "stopped"
        }
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        raise HTTPException(status_code=500, detail={"message": f"Failed to get status: {e}"})

# Helper functions

def _find_most_active_participant(participants: List[Dict]) -> Optional[Dict]:
    """Find the most active participant"""
    if not participants:
        return None
    
    return max(participants, key=lambda p: p.get("contribution_score", 0))

def _calculate_engagement_distribution(participants: List[Dict]) -> Dict[str, int]:
    """Calculate engagement level distribution"""
    distribution = {"high": 0, "medium": 0, "low": 0}
    
    for participant in participants:
        level = participant.get("engagement_level", "medium")
        if level in distribution:
            distribution[level] += 1
    
    return distribution

def _find_most_discussed_topic(topics: List[Dict]) -> Optional[Dict]:
    """Find the most discussed topic"""
    if not topics:
        return None
    
    return max(topics, key=lambda t: t.get("duration", 0))

def _categorize_topics(topics: List[Dict]) -> Dict[str, int]:
    """Categorize topics by type"""
    categories = {}
    
    for topic in topics:
        topic_name = topic.get("topic", "Unknown")
        # Simple categorization based on topic name
        if any(word in topic_name.lower() for word in ["code", "development", "programming"]):
            category = "Development"
        elif any(word in topic_name.lower() for word in ["plan", "project", "timeline"]):
            category = "Planning"
        elif any(word in topic_name.lower() for word in ["review", "feedback", "discussion"]):
            category = "Review"
        else:
            category = "General"
        
        categories[category] = categories.get(category, 0) + 1
    
    return categories

def _calculate_topic_time_distribution(topics: List[Dict]) -> List[Dict]:
    """Calculate time distribution for topics"""
    return [
        {
            "topic": topic.get("topic"),
            "duration": topic.get("duration", 0),
            "percentage": (topic.get("duration", 0) / sum(t.get("duration", 0) for t in topics)) * 100 if topics else 0
        }
        for topic in topics
    ]

def _calculate_average_confidence(items: List[Dict]) -> float:
    """Calculate average confidence score"""
    if not items:
        return 0.0
    
    confidences = [item.get("confidence", 0) for item in items]
    return sum(confidences) / len(confidences)

def _calculate_priority_distribution(items: List[Dict]) -> Dict[str, int]:
    """Calculate priority distribution"""
    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0, "urgent": 0}
    
    for item in items:
        priority = item.get("priority", "medium")
        if priority in distribution:
            distribution[priority] += 1
    
    return distribution

def _calculate_assignee_distribution(action_items: List[Dict]) -> Dict[str, int]:
    """Calculate assignee distribution for action items"""
    distribution = {}
    
    for item in action_items:
        assignee = item.get("assignee", "Unassigned")
        distribution[assignee] = distribution.get(assignee, 0) + 1
    
    return distribution

def _interpret_trend(metric: str, trend_value: float) -> str:
    """Interpret trend value for human-readable insights"""
    if abs(trend_value) < 2:
        return f"{metric.capitalize()} has remained stable with minimal change"
    elif trend_value > 5:
        return f"{metric.capitalize()} is showing strong improvement"
    elif trend_value > 2:
        return f"{metric.capitalize()} is showing moderate improvement"
    elif trend_value < -5:
        return f"{metric.capitalize()} is declining significantly"
    elif trend_value < -2:
        return f"{metric.capitalize()} is showing moderate decline"
    else:
        return f"{metric.capitalize()} trend is unclear"
