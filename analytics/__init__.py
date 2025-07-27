"""
VoiceLink Analytics Package

Comprehensive analytics extraction system for meeting intelligence.
"""

from .extraction_engine import AnalyticsExtractor, analytics_engine
from .service import AnalyticsService, analytics_service
from .models import *

__version__ = "1.0.0"
__all__ = [
    "AnalyticsExtractor",
    "analytics_engine", 
    "AnalyticsService", 
    "analytics_service",
    "MeetingAnalytics",
    "ParticipantAnalyticsDetail",
    "TopicAnalyticsDetail",
    "DecisionAnalyticsDetail",
    "ActionItemAnalyticsDetail"
]
