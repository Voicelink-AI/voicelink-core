"""
LLM Pipeline for VoiceLink

This module orchestrates the LLM processing pipeline for meeting transcripts.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Import LLM adapters with fallback handling
try:
    from .adapters import OpenAIAdapter, VertexAIAdapter, OPENAI_AVAILABLE, VERTEXAI_AVAILABLE
except ImportError:
    OPENAI_AVAILABLE = False
    VERTEXAI_AVAILABLE = False
    OpenAIAdapter = None
    VertexAIAdapter = None

from .utils import PromptLibrary

logger = logging.getLogger(__name__)


class LLMPipeline:
    """Main LLM processing pipeline for VoiceLink"""
    
    def __init__(self, config):
        self.config = config
        self.prompt_library = PromptLibrary()
        self.llm_adapter = None
        
        # Initialize LLM adapter based on configuration
        self._initialize_llm_adapter()
        
        logger.info("LLM Pipeline initialized")
    
    def _initialize_llm_adapter(self):
        """Initialize the appropriate LLM adapter based on configuration"""
        provider = os.getenv('LLM_PROVIDER', 'mock').lower()
        
        if provider == 'openai' and OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            model = os.getenv('OPENAI_MODEL', 'gpt-4')
            if api_key:
                self.llm_adapter = OpenAIAdapter(api_key=api_key, model=model)
                logger.info(f"Initialized OpenAI adapter with model: {model}")
            else:
                logger.warning("OpenAI API key not found, using mock mode")
        
        elif provider == 'vertexai' and VERTEXAI_AVAILABLE:
            project_id = os.getenv('GCP_PROJECT_ID')
            location = os.getenv('GCP_LOCATION', 'us-central1')
            model = os.getenv('VERTEXAI_MODEL', 'text-bison@001')
            if project_id:
                self.llm_adapter = VertexAIAdapter(
                    project_id=project_id,
                    location=location,
                    model_name=model
                )
                logger.info(f"Initialized VertexAI adapter with model: {model}")
            else:
                logger.warning("GCP project ID not found, using mock mode")
        
        else:
            logger.info(f"Using mock mode for LLM processing (provider: {provider})")
    
    def _use_mock_mode(self) -> bool:
        """Check if we should use mock mode"""
        return self.llm_adapter is None
    
    async def process_meeting(
        self,
        transcripts: List[Dict],
        code_context: Dict,
        participants: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process meeting transcripts through complete LLM pipeline"""
        try:
            logger.info("Starting LLM pipeline processing")
            
            if self._use_mock_mode():
                return self._mock_processing(transcripts, code_context, participants, metadata)
            
            # Real LLM processing
            return await self._real_processing(transcripts, code_context, participants, metadata)
            
        except Exception as e:
            logger.error(f"LLM pipeline processing failed: {e}")
            raise
    
    def _mock_processing(self, transcripts, code_context, participants, metadata) -> Dict[str, Any]:
        """Mock processing for development/testing"""
        results = {
            "meeting_summary": {
                "executive_summary": "Team discussed API redesign and sprint planning priorities.",
                "main_topics": [
                    "API redesign architecture",
                    "Authentication middleware updates"
                ]
            },
            "action_items": [
                {
                    "id": "action_1",
                    "description": "Review PR #234",
                    "assignee": "Alice",
                    "priority": "high"
                }
            ],
            "key_points": [
                "API redesign should prioritize security",
                "Authentication system needs updates"
            ],
            "processing_time": datetime.now().isoformat(),
            "provider": "mock"
        }
        
        logger.info("LLM pipeline processing completed (mock mode)")
        return results
    
    async def _real_processing(self, transcripts, code_context, participants, metadata) -> Dict[str, Any]:
        """Real LLM processing using configured adapter"""
        logger.info(f"Processing with real LLM adapter: {type(self.llm_adapter).__name__}")
        
        # Combine all transcripts into a single text
        full_transcript = self._combine_transcripts(transcripts)
        
        # Prepare prompts
        summary_prompt = self.prompt_library.get_prompt(
            "meeting_summary", 
            transcript=full_transcript, 
            participants=participants
        )
        
        action_items_prompt = self.prompt_library.get_prompt(
            "action_items",
            transcript=full_transcript
        )
        
        key_points_prompt = self.prompt_library.get_prompt(
            "key_points",
            transcript=full_transcript
        )
        
        # Process in parallel for efficiency
        tasks = []
        
        # Generate summary
        tasks.append(self.llm_adapter.generate_response(
            summary_prompt,
            temperature=0.7,
            max_tokens=1000
        ))
        
        # Extract action items  
        tasks.append(self.llm_adapter.extract_action_items(full_transcript))
        
        # Generate key points
        tasks.append(self.llm_adapter.generate_response(
            key_points_prompt,
            temperature=0.6,
            max_tokens=800
        ))
        
        # Execute all tasks in parallel
        summary_result, action_items, key_points_result = await asyncio.gather(*tasks)
        
        # Process code context if available
        code_analysis = {}
        if code_context and code_context.get('extracted_code'):
            code_analysis = await self.llm_adapter.analyze_code_context(
                code_context['extracted_code'],
                code_context.get('language', 'unknown')
            )
        
        # Format results
        results = {
            "meeting_summary": {
                "executive_summary": summary_result.get('content', ''),
                "main_topics": self._extract_topics_from_summary(summary_result.get('content', ''))
            },
            "action_items": action_items,
            "key_points": self._extract_bullet_points(key_points_result.get('content', '')),
            "code_analysis": code_analysis,
            "processing_time": datetime.now().isoformat(),
            "provider": type(self.llm_adapter).__name__,
            "token_usage": {
                "summary": summary_result.get('usage', {}),
                "key_points": key_points_result.get('usage', {}),
                "total_tokens": (
                    summary_result.get('usage', {}).get('total_tokens', 0) +
                    key_points_result.get('usage', {}).get('total_tokens', 0)
                )
            }
        }
        
        logger.info(f"LLM pipeline processing completed. Total tokens: {results['token_usage']['total_tokens']}")
        return results
    
    def _combine_transcripts(self, transcripts: List[Dict]) -> str:
        """Combine multiple transcript segments into a single text"""
        combined = []
        for transcript in transcripts:
            speaker = transcript.get('speaker', 'Unknown')
            text = transcript.get('text', '')
            timestamp = transcript.get('timestamp', '')
            
            combined.append(f"[{timestamp}] {speaker}: {text}")
        
        return "\n".join(combined)
    
    def _extract_topics_from_summary(self, summary: str) -> List[str]:
        """Extract main topics from generated summary"""
        # Simple extraction - in production, this could be more sophisticated
        topics = []
        lines = summary.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                topic = line.lstrip('•-* ').strip()
                if topic:
                    topics.append(topic)
        
        # If no bullet points found, create topics from sentences
        if not topics:
            sentences = summary.split('.')
            topics = [s.strip() for s in sentences[:3] if s.strip() and len(s.strip()) > 10]
        
        return topics[:5]  # Limit to 5 main topics
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                point = line.lstrip('•-* ').strip()
                if point:
                    points.append(point)
            elif line and not line.startswith('[') and len(line) > 20:  # Potential key point
                points.append(line)
        
        return points[:10]  # Limit to 10 key points
