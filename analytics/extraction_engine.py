"""
Analytics Extraction Engine for VoiceLink

This module processes meeting transcripts and audio data to extract:
- Participants and speaker identification
- Topics and themes discussed
- Key decisions made
- Action items and assignments
- Code context and technical discussions
- Meeting sentiment and engagement metrics
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AnalyticsType(Enum):
    PARTICIPANTS = "participants"
    TOPICS = "topics"
    DECISIONS = "decisions"
    ACTION_ITEMS = "action_items"
    CODE_CONTEXT = "code_context"
    SENTIMENT = "sentiment"
    ENGAGEMENT = "engagement"

@dataclass
class ParticipantAnalytics:
    speaker_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    speaking_time: float = 0.0
    contribution_score: float = 0.0
    engagement_level: str = "medium"  # low, medium, high
    topics_contributed: List[str] = None

@dataclass
class TopicAnalytics:
    topic: str
    confidence: float
    duration: float
    participants: List[str]
    keywords: List[str]
    importance_score: float

@dataclass
class DecisionAnalytics:
    decision: str
    confidence: float
    timestamp: float
    participants_involved: List[str]
    context: str
    priority: str  # low, medium, high, critical

@dataclass
class ActionItemAnalytics:
    task: str
    assignee: Optional[str]
    due_date: Optional[str]
    priority: str
    status: str = "open"
    context: str = ""
    estimated_effort: Optional[str] = None

@dataclass
class CodeContextAnalytics:
    code_references: List[str]
    repositories_mentioned: List[str]
    technical_terms: List[str]
    api_discussions: List[str]
    architecture_decisions: List[str]
    bug_reports: List[str]

class AnalyticsExtractor:
    """Main analytics extraction engine"""
    
    def __init__(self):
        self.extractors = {
            AnalyticsType.PARTICIPANTS: ParticipantExtractor(),
            AnalyticsType.TOPICS: TopicExtractor(),
            AnalyticsType.DECISIONS: DecisionExtractor(),
            AnalyticsType.ACTION_ITEMS: ActionItemExtractor(),
            AnalyticsType.CODE_CONTEXT: CodeContextExtractor(),
            AnalyticsType.SENTIMENT: SentimentExtractor(),
            AnalyticsType.ENGAGEMENT: EngagementExtractor()
        }
    
    async def extract_all_analytics(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all analytics from meeting data"""
        logger.info(f"Starting analytics extraction for meeting {meeting_data.get('meeting_id')}")
        
        results = {}
        
        for analytics_type, extractor in self.extractors.items():
            try:
                logger.debug(f"Extracting {analytics_type.value} analytics...")
                results[analytics_type.value] = await extractor.extract(meeting_data)
                logger.debug(f"✅ {analytics_type.value} extraction completed")
            except Exception as e:
                logger.error(f"❌ Error extracting {analytics_type.value}: {e}")
                results[analytics_type.value] = None
        
        # Calculate aggregated metrics
        results["aggregated_metrics"] = self._calculate_aggregated_metrics(results)
        
        logger.info("Analytics extraction completed successfully")
        return results
    
    def _calculate_aggregated_metrics(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall meeting metrics"""
        try:
            participants_data = analytics.get("participants", [])
            topics_data = analytics.get("topics", [])
            decisions_data = analytics.get("decisions", [])
            action_items_data = analytics.get("action_items", [])
            
            return {
                "total_participants": len(participants_data) if participants_data else 0,
                "total_topics": len(topics_data) if topics_data else 0,
                "total_decisions": len(decisions_data) if decisions_data else 0,
                "total_action_items": len(action_items_data) if action_items_data else 0,
                "meeting_productivity_score": self._calculate_productivity_score(analytics),
                "engagement_score": self._calculate_engagement_score(analytics),
                "technical_complexity": self._calculate_technical_complexity(analytics)
            }
        except Exception as e:
            logger.error(f"Error calculating aggregated metrics: {e}")
            return {}
    
    def _calculate_productivity_score(self, analytics: Dict[str, Any]) -> float:
        """Calculate overall meeting productivity score (0-100)"""
        try:
            decisions = len(analytics.get("decisions", []))
            action_items = len(analytics.get("action_items", []))
            topics = len(analytics.get("topics", []))
            
            # Weighted scoring
            score = (decisions * 30) + (action_items * 25) + (min(topics, 5) * 9)
            return min(score, 100.0)
        except:
            return 50.0  # Default moderate score
    
    def _calculate_engagement_score(self, analytics: Dict[str, Any]) -> float:
        """Calculate overall engagement score (0-100)"""
        try:
            participants = analytics.get("participants", [])
            if not participants:
                return 50.0
            
            total_engagement = sum(p.get("contribution_score", 0) for p in participants)
            return min(total_engagement / len(participants) * 20, 100.0)
        except:
            return 50.0
    
    def _calculate_technical_complexity(self, analytics: Dict[str, Any]) -> str:
        """Calculate technical complexity level"""
        try:
            code_context = analytics.get("code_context", {})
            if not code_context:
                return "low"
            
            code_refs = len(code_context.get("code_references", []))
            tech_terms = len(code_context.get("technical_terms", []))
            
            if code_refs > 10 or tech_terms > 20:
                return "high"
            elif code_refs > 3 or tech_terms > 8:
                return "medium"
            else:
                return "low"
        except:
            return "low"

class ParticipantExtractor:
    """Extract participant analytics"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        transcripts = meeting_data.get("transcripts", [])
        speaker_segments = meeting_data.get("speaker_segments", [])
        
        participants = {}
        
        # Analyze each transcript
        for transcript in transcripts:
            speaker_id = transcript.get("speaker_id", "unknown")
            text = transcript.get("text", "")
            duration = transcript.get("end_time", 0) - transcript.get("start_time", 0)
            
            if speaker_id not in participants:
                participants[speaker_id] = {
                    "speaker_id": speaker_id,
                    "name": self._extract_speaker_name(text, speaker_id),
                    "speaking_time": 0.0,
                    "word_count": 0,
                    "contribution_score": 0.0,
                    "topics_contributed": set(),
                    "engagement_indicators": []
                }
            
            participants[speaker_id]["speaking_time"] += duration
            participants[speaker_id]["word_count"] += len(text.split())
            
            # Detect engagement indicators
            engagement = self._analyze_engagement(text)
            participants[speaker_id]["engagement_indicators"].extend(engagement)
        
        # Calculate final metrics
        for participant in participants.values():
            participant["contribution_score"] = self._calculate_contribution_score(participant)
            participant["engagement_level"] = self._determine_engagement_level(participant)
            participant["topics_contributed"] = list(participant["topics_contributed"])
            del participant["engagement_indicators"]  # Remove internal data
        
        return list(participants.values())
    
    def _extract_speaker_name(self, text: str, speaker_id: str) -> Optional[str]:
        """Try to extract actual speaker name from context"""
        # Look for introductions like "Hi, I'm John" or "This is Sarah"
        name_patterns = [
            r"(?:I'm|I am|This is|My name is)\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s+(?:here|speaking)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return f"Speaker {speaker_id}"
    
    def _analyze_engagement(self, text: str) -> List[str]:
        """Analyze text for engagement indicators"""
        indicators = []
        text_lower = text.lower()
        
        # Question asking
        if "?" in text or any(word in text_lower for word in ["what", "how", "why", "when", "where"]):
            indicators.append("asks_questions")
        
        # Agreement/disagreement
        if any(word in text_lower for word in ["agree", "disagree", "exactly", "right", "correct"]):
            indicators.append("expresses_opinion")
        
        # Technical contribution
        if any(word in text_lower for word in ["code", "function", "api", "database", "algorithm"]):
            indicators.append("technical_contribution")
        
        # Action orientation
        if any(word in text_lower for word in ["should", "will", "need to", "let's", "action"]):
            indicators.append("action_oriented")
        
        return indicators
    
    def _calculate_contribution_score(self, participant: Dict[str, Any]) -> float:
        """Calculate participant contribution score (0-10)"""
        speaking_time = participant["speaking_time"]
        word_count = participant["word_count"]
        engagement_count = len(participant.get("engagement_indicators", []))
        
        # Normalize and weight factors
        time_score = min(speaking_time / 300, 1.0) * 3  # Max 3 points for 5+ minutes
        word_score = min(word_count / 500, 1.0) * 4     # Max 4 points for 500+ words
        engagement_score = min(engagement_count / 5, 1.0) * 3  # Max 3 points for 5+ indicators
        
        return round(time_score + word_score + engagement_score, 2)
    
    def _determine_engagement_level(self, participant: Dict[str, Any]) -> str:
        """Determine engagement level based on contribution score"""
        score = participant["contribution_score"]
        if score >= 7:
            return "high"
        elif score >= 4:
            return "medium"
        else:
            return "low"

class TopicExtractor:
    """Extract topics and themes from meeting content"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        transcripts = meeting_data.get("transcripts", [])
        
        # Combine all transcript text
        full_text = " ".join(transcript.get("text", "") for transcript in transcripts)
        
        # Extract topics using keyword analysis and semantic grouping
        topics = []
        
        # Predefined topic categories with keywords
        topic_categories = {
            "Project Planning": ["project", "plan", "timeline", "milestone", "deadline", "schedule"],
            "Code Review": ["code", "review", "pull request", "merge", "branch", "commit"],
            "Bug Discussion": ["bug", "issue", "problem", "error", "fix", "debug"],
            "Feature Development": ["feature", "requirement", "implement", "develop", "build"],
            "Testing": ["test", "testing", "qa", "quality", "validation", "coverage"],
            "Deployment": ["deploy", "deployment", "release", "production", "staging"],
            "Architecture": ["architecture", "design", "pattern", "structure", "framework"],
            "Performance": ["performance", "optimization", "speed", "memory", "efficiency"],
            "Security": ["security", "authentication", "authorization", "vulnerability"],
            "Database": ["database", "sql", "query", "schema", "migration"],
            "API": ["api", "endpoint", "rest", "graphql", "integration"],
            "Documentation": ["documentation", "docs", "readme", "wiki", "guide"]
        }
        
        for topic_name, keywords in topic_categories.items():
            score = self._calculate_topic_score(full_text, keywords)
            if score > 0.1:  # Threshold for topic relevance
                duration = self._estimate_topic_duration(transcripts, keywords)
                participants = self._find_topic_participants(transcripts, keywords)
                
                topics.append({
                    "topic": topic_name,
                    "confidence": score,
                    "duration": duration,
                    "participants": participants,
                    "keywords": [kw for kw in keywords if kw.lower() in full_text.lower()],
                    "importance_score": score * (1 + len(participants) * 0.2)
                })
        
        # Sort by importance score
        topics.sort(key=lambda x: x["importance_score"], reverse=True)
        return topics[:10]  # Return top 10 topics
    
    def _calculate_topic_score(self, text: str, keywords: List[str]) -> float:
        """Calculate topic relevance score"""
        text_lower = text.lower()
        word_count = len(text.split())
        
        if word_count == 0:
            return 0.0
        
        keyword_matches = sum(text_lower.count(keyword.lower()) for keyword in keywords)
        return min(keyword_matches / word_count * 100, 1.0)
    
    def _estimate_topic_duration(self, transcripts: List[Dict], keywords: List[str]) -> float:
        """Estimate how long topic was discussed"""
        total_duration = 0.0
        
        for transcript in transcripts:
            text = transcript.get("text", "").lower()
            if any(keyword.lower() in text for keyword in keywords):
                duration = transcript.get("end_time", 0) - transcript.get("start_time", 0)
                total_duration += duration
        
        return total_duration
    
    def _find_topic_participants(self, transcripts: List[Dict], keywords: List[str]) -> List[str]:
        """Find which participants discussed this topic"""
        participants = set()
        
        for transcript in transcripts:
            text = transcript.get("text", "").lower()
            if any(keyword.lower() in text for keyword in keywords):
                speaker_id = transcript.get("speaker_id", "unknown")
                participants.add(speaker_id)
        
        return list(participants)

class DecisionExtractor:
    """Extract key decisions made during the meeting"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        transcripts = meeting_data.get("transcripts", [])
        decisions = []
        
        # Decision indicator patterns
        decision_patterns = [
            r"(?:we (?:decided|agreed|concluded|determined))\s+(?:to|that)\s+([^.!?]+)",
            r"(?:let's|we'll|we will|we should)\s+([^.!?]+)",
            r"(?:the decision is|we've decided)\s+([^.!?]+)",
            r"(?:action item|ai):\s*([^.!?]+)",
            r"(?:resolved|settled|finalized):\s*([^.!?]+)"
        ]
        
        for transcript in transcripts:
            text = transcript.get("text", "")
            timestamp = transcript.get("start_time", 0)
            speaker_id = transcript.get("speaker_id", "unknown")
            
            for pattern in decision_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    decision_text = match.group(1).strip()
                    if len(decision_text) > 10:  # Filter out very short matches
                        
                        priority = self._determine_priority(decision_text, text)
                        confidence = self._calculate_decision_confidence(decision_text, text)
                        
                        decisions.append({
                            "decision": decision_text,
                            "confidence": confidence,
                            "timestamp": timestamp,
                            "participants_involved": [speaker_id],
                            "context": text[:200] + "..." if len(text) > 200 else text,
                            "priority": priority
                        })
        
        # Remove duplicates and merge similar decisions
        decisions = self._deduplicate_decisions(decisions)
        
        # Sort by confidence and priority
        decisions.sort(key=lambda x: (x["confidence"], self._priority_weight(x["priority"])), reverse=True)
        
        return decisions[:15]  # Return top 15 decisions
    
    def _determine_priority(self, decision: str, context: str) -> str:
        """Determine decision priority based on keywords"""
        high_priority_keywords = ["urgent", "critical", "asap", "immediately", "deadline", "blocking"]
        medium_priority_keywords = ["important", "should", "need", "required", "must"]
        
        decision_lower = decision.lower()
        context_lower = context.lower()
        
        if any(keyword in decision_lower or keyword in context_lower for keyword in high_priority_keywords):
            return "critical"
        elif any(keyword in decision_lower or keyword in context_lower for keyword in medium_priority_keywords):
            return "high"
        elif any(keyword in decision_lower for keyword in ["will", "going to", "plan"]):
            return "medium"
        else:
            return "low"
    
    def _calculate_decision_confidence(self, decision: str, context: str) -> float:
        """Calculate confidence score for decision (0-1)"""
        confidence_indicators = ["decided", "agreed", "confirmed", "final", "definitely"]
        uncertainty_indicators = ["maybe", "perhaps", "might", "could", "possibly"]
        
        decision_lower = decision.lower()
        context_lower = context.lower()
        
        confidence_score = 0.5  # Base confidence
        
        # Increase confidence for strong indicators
        for indicator in confidence_indicators:
            if indicator in context_lower:
                confidence_score += 0.15
        
        # Decrease confidence for uncertainty indicators
        for indicator in uncertainty_indicators:
            if indicator in decision_lower or indicator in context_lower:
                confidence_score -= 0.2
        
        return max(0.1, min(1.0, confidence_score))
    
    def _deduplicate_decisions(self, decisions: List[Dict]) -> List[Dict]:
        """Remove duplicate or very similar decisions"""
        unique_decisions = []
        
        for decision in decisions:
            is_duplicate = False
            decision_text = decision["decision"].lower()
            
            for existing in unique_decisions:
                existing_text = existing["decision"].lower()
                # Simple similarity check based on common words
                if self._calculate_text_similarity(decision_text, existing_text) > 0.7:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if decision["confidence"] > existing["confidence"]:
                        unique_decisions.remove(existing)
                        unique_decisions.append(decision)
                    break
            
            if not is_duplicate:
                unique_decisions.append(decision)
        
        return unique_decisions
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _priority_weight(self, priority: str) -> int:
        """Convert priority to numeric weight for sorting"""
        weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        return weights.get(priority, 1)

class ActionItemExtractor:
    """Extract action items and assignments"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        transcripts = meeting_data.get("transcripts", [])
        action_items = []
        
        # Action item patterns
        action_patterns = [
            r"(?:action item|ai|todo|task):\s*([^.!?]+)",
            r"(?:@\w+|[A-Z][a-z]+)\s+(?:will|should|needs to|has to)\s+([^.!?]+)",
            r"(?:we need|someone should|please)\s+([^.!?]+)",
            r"(?:by|due|deadline)\s+(\w+\s+\d+|\d+[/-]\d+[/-]\d+)\s*:?\s*([^.!?]+)",
            r"(?:assigned to|owner|responsible):\s*(\w+)\s*-?\s*([^.!?]+)"
        ]
        
        for transcript in transcripts:
            text = transcript.get("text", "")
            speaker_id = transcript.get("speaker_id", "unknown")
            
            for pattern in action_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 1:
                        task = match.group(-1).strip()  # Last group is usually the task
                        
                        if len(task) > 5:  # Filter very short tasks
                            assignee = self._extract_assignee(match, text, speaker_id)
                            due_date = self._extract_due_date(match, text)
                            priority = self._determine_task_priority(task, text)
                            effort = self._estimate_effort(task)
                            
                            action_items.append({
                                "task": task,
                                "assignee": assignee,
                                "due_date": due_date,
                                "priority": priority,
                                "status": "open",
                                "context": text[:150] + "..." if len(text) > 150 else text,
                                "estimated_effort": effort
                            })
        
        # Remove duplicates
        action_items = self._deduplicate_action_items(action_items)
        
        return action_items[:20]  # Return top 20 action items
    
    def _extract_assignee(self, match, text: str, default_speaker: str) -> Optional[str]:
        """Extract assignee from the match or surrounding text"""
        # Look for @mentions or names in the match
        assignee_patterns = [
            r"@(\w+)",
            r"([A-Z][a-z]+)\s+(?:will|should)",
            r"assigned to\s+(\w+)"
        ]
        
        full_text = match.group(0) + " " + text
        
        for pattern in assignee_patterns:
            assignee_match = re.search(pattern, full_text, re.IGNORECASE)
            if assignee_match:
                return assignee_match.group(1)
        
        # If no specific assignee found, check if speaker is volunteering
        volunteer_indicators = ["i will", "i'll", "i can", "i should"]
        text_lower = text.lower()
        
        if any(indicator in text_lower for indicator in volunteer_indicators):
            return default_speaker
        
        return None
    
    def _extract_due_date(self, match, text: str) -> Optional[str]:
        """Extract due date from text"""
        date_patterns = [
            r"(?:by|due|deadline)\s+(\w+\s+\d+)",  # "by Friday 15"
            r"(\d+[/-]\d+[/-]\d+)",               # "12/25/2023"
            r"(next \w+)",                         # "next week"
            r"(end of \w+)",                       # "end of week"
            r"(tomorrow|today)"                    # "tomorrow"
        ]
        
        full_text = match.group(0) + " " + text
        
        for pattern in date_patterns:
            date_match = re.search(pattern, full_text, re.IGNORECASE)
            if date_match:
                return date_match.group(1).strip()
        
        return None
    
    def _determine_task_priority(self, task: str, context: str) -> str:
        """Determine task priority"""
        urgent_keywords = ["urgent", "asap", "immediately", "critical", "blocking"]
        high_keywords = ["important", "soon", "priority", "key"]
        
        task_lower = task.lower()
        context_lower = context.lower()
        
        if any(keyword in task_lower or keyword in context_lower for keyword in urgent_keywords):
            return "urgent"
        elif any(keyword in task_lower or keyword in context_lower for keyword in high_keywords):
            return "high"
        else:
            return "medium"
    
    def _estimate_effort(self, task: str) -> Optional[str]:
        """Estimate effort required for task"""
        task_lower = task.lower()
        
        # Large effort indicators
        if any(keyword in task_lower for keyword in ["implement", "build", "create", "develop", "design"]):
            return "large"
        
        # Small effort indicators
        elif any(keyword in task_lower for keyword in ["update", "fix", "change", "review", "send"]):
            return "small"
        
        # Medium by default
        else:
            return "medium"
    
    def _deduplicate_action_items(self, action_items: List[Dict]) -> List[Dict]:
        """Remove duplicate action items"""
        unique_items = []
        
        for item in action_items:
            is_duplicate = False
            task_text = item["task"].lower()
            
            for existing in unique_items:
                existing_task = existing["task"].lower()
                if self._calculate_task_similarity(task_text, existing_task) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_items.append(item)
        
        return unique_items
    
    def _calculate_task_similarity(self, task1: str, task2: str) -> float:
        """Calculate task similarity"""
        words1 = set(task1.split())
        words2 = set(task2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

class CodeContextExtractor:
    """Extract code and technical context from discussions"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        transcripts = meeting_data.get("transcripts", [])
        
        # Combine all text
        full_text = " ".join(transcript.get("text", "") for transcript in transcripts)
        
        return {
            "code_references": self._extract_code_references(full_text),
            "repositories_mentioned": self._extract_repositories(full_text),
            "technical_terms": self._extract_technical_terms(full_text),
            "api_discussions": self._extract_api_discussions(full_text),
            "architecture_decisions": self._extract_architecture_decisions(full_text),
            "bug_reports": self._extract_bug_reports(full_text)
        }
    
    def _extract_code_references(self, text: str) -> List[str]:
        """Extract code-related references"""
        code_patterns = [
            r"(?:function|method|class)\s+(\w+)",
            r"(\w+\.\w+\(\))",  # method calls
            r"(\w+\.\w+)",      # object.property
            r"`([^`]+)`",       # code in backticks
            r"\/\*.*?\*\/",     # comments
            r"\/\/.*"           # single line comments
        ]
        
        references = []
        for pattern in code_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))[:20]  # Remove duplicates, limit to 20
    
    def _extract_repositories(self, text: str) -> List[str]:
        """Extract repository mentions"""
        repo_patterns = [
            r"(?:github\.com/|gitlab\.com/|bitbucket\.org/)([^\s]+)",
            r"(?:repo|repository|project)\s+([a-zA-Z0-9_-]+)",
            r"([a-zA-Z0-9_-]+)\.git"
        ]
        
        repos = []
        for pattern in repo_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            repos.extend(matches)
        
        return list(set(repos))[:10]
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terminology"""
        technical_keywords = [
            "api", "database", "backend", "frontend", "microservice", "docker", 
            "kubernetes", "aws", "azure", "gcp", "rest", "graphql", "sql",
            "nosql", "redis", "mongodb", "postgresql", "mysql", "nginx",
            "apache", "linux", "windows", "macos", "ios", "android", "react",
            "angular", "vue", "node", "python", "java", "javascript", "typescript",
            "golang", "rust", "c++", "c#", "ruby", "php", "scala", "kotlin"
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in technical_keywords:
            if term in text_lower:
                # Count occurrences
                count = text_lower.count(term)
                if count > 0:
                    found_terms.append({"term": term, "count": count})
        
        # Sort by frequency
        found_terms.sort(key=lambda x: x["count"], reverse=True)
        return [term["term"] for term in found_terms[:15]]
    
    def _extract_api_discussions(self, text: str) -> List[str]:
        """Extract API-related discussions"""
        api_patterns = [
            r"(?:api|endpoint)\s+([^\s.!?]+)",
            r"(?:get|post|put|delete|patch)\s+([^\s.!?]+)",
            r"\/api\/([^\s.!?]+)",
            r"(?:response|request)\s+([^\s.!?]+)"
        ]
        
        discussions = []
        for pattern in api_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            discussions.extend(matches)
        
        return list(set(discussions))[:10]
    
    def _extract_architecture_decisions(self, text: str) -> List[str]:
        """Extract architecture-related decisions"""
        arch_keywords = [
            "architecture", "design pattern", "microservice", "monolith",
            "scalability", "performance", "security", "deployment", "infrastructure"
        ]
        
        decisions = []
        text_lower = text.lower()
        
        for keyword in arch_keywords:
            if keyword in text_lower:
                # Find sentences containing the keyword
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        decisions.append(sentence.strip())
        
        return decisions[:8]
    
    def _extract_bug_reports(self, text: str) -> List[str]:
        """Extract bug reports and issues"""
        bug_patterns = [
            r"(?:bug|issue|problem|error)\s*[:#-]?\s*([^.!?]+)",
            r"(?:not working|broken|failing)\s*[:#-]?\s*([^.!?]+)",
            r"(?:fix|resolve|debug)\s*[:#-]?\s*([^.!?]+)"
        ]
        
        bugs = []
        for pattern in bug_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            bugs.extend(matches)
        
        return list(set(bugs))[:10]

class SentimentExtractor:
    """Extract sentiment and emotional tone from meeting"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        transcripts = meeting_data.get("transcripts", [])
        
        positive_words = [
            "great", "excellent", "awesome", "perfect", "love", "excited",
            "happy", "good", "nice", "wonderful", "fantastic", "brilliant"
        ]
        
        negative_words = [
            "bad", "terrible", "awful", "hate", "frustrated", "angry",
            "sad", "worried", "concerned", "problem", "issue", "difficult"
        ]
        
        neutral_words = [
            "okay", "fine", "normal", "standard", "regular", "typical"
        ]
        
        sentiment_scores = []
        overall_positive = 0
        overall_negative = 0
        overall_neutral = 0
        
        for transcript in transcripts:
            text = transcript.get("text", "").lower()
            words = text.split()
            
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            neutral_count = sum(1 for word in words if word in neutral_words)
            
            total_sentiment_words = positive_count + negative_count + neutral_count
            
            if total_sentiment_words > 0:
                segment_sentiment = {
                    "speaker_id": transcript.get("speaker_id"),
                    "positive": positive_count / total_sentiment_words,
                    "negative": negative_count / total_sentiment_words,
                    "neutral": neutral_count / total_sentiment_words,
                    "timestamp": transcript.get("start_time", 0)
                }
                sentiment_scores.append(segment_sentiment)
            
            overall_positive += positive_count
            overall_negative += negative_count
            overall_neutral += neutral_count
        
        total_sentiment = overall_positive + overall_negative + overall_neutral
        
        if total_sentiment > 0:
            overall_sentiment = {
                "positive": overall_positive / total_sentiment,
                "negative": overall_negative / total_sentiment,
                "neutral": overall_neutral / total_sentiment
            }
        else:
            overall_sentiment = {"positive": 0.33, "negative": 0.33, "neutral": 0.34}
        
        # Determine overall mood
        if overall_sentiment["positive"] > 0.5:
            mood = "positive"
        elif overall_sentiment["negative"] > 0.4:
            mood = "negative"
        else:
            mood = "neutral"
        
        return {
            "overall_sentiment": overall_sentiment,
            "mood": mood,
            "sentiment_timeline": sentiment_scores,
            "emotional_keywords": {
                "positive_indicators": [w for w in positive_words if w in " ".join(t.get("text", "") for t in transcripts).lower()],
                "negative_indicators": [w for w in negative_words if w in " ".join(t.get("text", "") for t in transcripts).lower()]
            }
        }

class EngagementExtractor:
    """Extract engagement metrics from meeting"""
    
    async def extract(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        transcripts = meeting_data.get("transcripts", [])
        audio_info = meeting_data.get("audio_info", {})
        
        total_duration = audio_info.get("duration_seconds", 0)
        speaker_stats = {}
        
        # Calculate speaking distribution
        for transcript in transcripts:
            speaker_id = transcript.get("speaker_id", "unknown")
            duration = transcript.get("end_time", 0) - transcript.get("start_time", 0)
            
            if speaker_id not in speaker_stats:
                speaker_stats[speaker_id] = {
                    "speaking_time": 0,
                    "turn_count": 0,
                    "interruptions": 0,
                    "questions_asked": 0
                }
            
            speaker_stats[speaker_id]["speaking_time"] += duration
            speaker_stats[speaker_id]["turn_count"] += 1
            
            # Count questions
            text = transcript.get("text", "")
            questions = text.count("?")
            speaker_stats[speaker_id]["questions_asked"] += questions
        
        # Calculate engagement metrics
        if total_duration > 0:
            for speaker_id, stats in speaker_stats.items():
                stats["speaking_percentage"] = (stats["speaking_time"] / total_duration) * 100
                stats["average_turn_length"] = stats["speaking_time"] / max(stats["turn_count"], 1)
        
        # Overall engagement metrics
        total_speakers = len(speaker_stats)
        total_turns = sum(stats["turn_count"] for stats in speaker_stats.values())
        total_questions = sum(stats["questions_asked"] for stats in speaker_stats.values())
        
        engagement_score = min(100, (total_turns * 2) + (total_questions * 5) + (total_speakers * 10))
        
        return {
            "engagement_score": engagement_score,
            "total_speakers": total_speakers,
            "total_speaking_turns": total_turns,
            "total_questions_asked": total_questions,
            "speaker_distribution": speaker_stats,
            "meeting_dynamics": {
                "balanced_participation": self._assess_participation_balance(speaker_stats),
                "interaction_level": "high" if total_questions > 10 else "medium" if total_questions > 3 else "low",
                "discussion_flow": "interactive" if total_turns > total_speakers * 3 else "presentation-style"
            }
        }
    
    def _assess_participation_balance(self, speaker_stats: Dict) -> str:
        """Assess how balanced the participation was"""
        if not speaker_stats:
            return "unknown"
        
        speaking_percentages = [stats.get("speaking_percentage", 0) for stats in speaker_stats.values()]
        
        if not speaking_percentages:
            return "unknown"
        
        max_percentage = max(speaking_percentages)
        min_percentage = min(speaking_percentages)
        
        if max_percentage - min_percentage < 20:
            return "balanced"
        elif max_percentage > 70:
            return "dominated"
        else:
            return "moderate"

# Global analytics engine instance
analytics_engine = AnalyticsExtractor()
