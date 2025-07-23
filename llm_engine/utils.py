"""
LLM Engine Utilities

Utility functions for prompt management, response parsing, and LLM operations.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Template class for managing LLM prompts"""
    
    def __init__(self, template: str, required_vars: List[str] = None):
        self.template = template
        self.required_vars = required_vars or []
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables"""
        # Check required variables
        missing_vars = [var for var in self.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")


class ResponseParser:
    """Parser for structured LLM responses"""
    
    @staticmethod
    def parse_bullet_points(text: str) -> List[str]:
        """Extract bullet points from text"""
        lines = text.split('\n')
        bullet_points = []
        
        for line in lines:
            line = line.strip()
            # Match various bullet point formats
            if re.match(r'^[-*•]\s+', line):
                bullet_points.append(re.sub(r'^[-*•]\s+', '', line).strip())
            elif re.match(r'^\d+\.\s+', line):
                bullet_points.append(re.sub(r'^\d+\.\s+', '', line).strip())
        
        return bullet_points
    
    @staticmethod
    def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response"""
        # Find JSON blocks
        json_match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from response")
        
        # Try to parse the entire text as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON")
            return None
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Tuple[str, str]]:
        """Extract code blocks with language identifiers"""
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        return [(lang or 'text', code.strip()) for lang, code in matches]
    
    @staticmethod
    def clean_response(text: str) -> str:
        """Clean and normalize LLM response text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove common LLM artifacts
        text = re.sub(r'^(Here\'s|Here is|I\'ll|I will)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+(Let me know|Feel free|Please let me know).*$', '', text, flags=re.IGNORECASE)
        
        return text.strip()


class PromptLibrary:
    """Library of pre-defined prompts for common tasks"""
    
    MEETING_SUMMARY = PromptTemplate(
        template="""
Analyze the following meeting transcript and provide a comprehensive summary.

Participants: {participants}
Duration: {duration} minutes
Date: {date}

Transcript:
{transcript}

Code Context:
{code_context}

Please provide:
1. Executive Summary (2-3 sentences)
2. Main Discussion Topics
3. Key Decisions Made
4. Technical Details Discussed
5. Action Items with Owners
6. Next Steps

Format your response in clear sections with bullet points where appropriate.
        """,
        required_vars=["participants", "duration", "transcript", "code_context"]
    )
    
    ACTION_ITEMS = PromptTemplate(
        template="""
Extract clear, actionable items from the following meeting transcript.

Transcript:
{transcript}

Focus on:
- Tasks assigned to specific people
- Follow-up actions needed
- Deadlines mentioned
- Commitments made

Format as bullet points with assignee when mentioned:
- [Assignee]: Action item description (Deadline if mentioned)

Action Items:
        """,
        required_vars=["transcript"]
    )
    
    KEY_POINTS = PromptTemplate(
        template="""
Extract the most important discussion points from this meeting transcript.

Transcript:
{transcript}

Focus on:
- Important decisions
- Key insights shared
- Problems identified
- Solutions proposed
- Technical details discussed

Format as bullet points (maximum 8 points):
        """,
        required_vars=["transcript"]
    )
    
    CODE_ANALYSIS = PromptTemplate(
        template="""
Analyze the following transcript for code-related discussions.

Transcript:
{transcript}

Code Context:
- Files mentioned: {files}
- Functions discussed: {functions}
- PR references: {prs}
- Issue references: {issues}

Please identify:
1. Code changes discussed
2. Implementation details
3. Technical decisions made
4. Code review feedback
5. Architecture discussions

Format as structured bullet points:
        """,
        required_vars=["transcript", "files", "functions", "prs", "issues"]
    )
    
    DOCUMENTATION_GENERATION = PromptTemplate(
        template="""
Generate technical documentation based on this meeting discussion.

Meeting Summary:
{summary}

Key Points:
{key_points}

Code Context:
{code_context}

Please generate:
1. Technical Overview
2. Implementation Details
3. API Changes (if any)
4. Configuration Changes
5. Testing Notes
6. Deployment Considerations

Format as structured documentation with clear headings and code examples where appropriate.
        """,
        required_vars=["summary", "key_points", "code_context"]
    )


class LLMMetrics:
    """Metrics tracking for LLM operations"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost = 0.0
        self.provider_usage = {}
        self.start_time = datetime.now()
    
    def record_request(self, provider: str, success: bool, tokens: Dict[str, int] = None, cost: float = 0.0):
        """Record a request"""
        self.requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        if tokens:
            self.total_tokens += tokens.get('total_tokens', 0)
            self.prompt_tokens += tokens.get('prompt_tokens', 0)
            self.completion_tokens += tokens.get('completion_tokens', 0)
        
        self.total_cost += cost
        
        # Track provider usage
        if provider not in self.provider_usage:
            self.provider_usage[provider] = {'requests': 0, 'tokens': 0, 'cost': 0.0}
        
        self.provider_usage[provider]['requests'] += 1
        if tokens:
            self.provider_usage[provider]['tokens'] += tokens.get('total_tokens', 0)
        self.provider_usage[provider]['cost'] += cost
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        runtime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "runtime_seconds": runtime,
            "total_requests": self.requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.successful_requests / self.requests if self.requests > 0 else 0,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost": self.total_cost,
            "average_tokens_per_request": self.total_tokens / self.requests if self.requests > 0 else 0,
            "requests_per_second": self.requests / runtime if runtime > 0 else 0,
            "provider_usage": self.provider_usage
        }


def estimate_token_count(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Estimate token count for text (rough approximation)"""
    # Very rough estimation: ~4 characters per token for English text
    # This is not accurate but gives a ballpark figure
    char_count = len(text)
    estimated_tokens = char_count // 4
    
    # Add some overhead for chat formatting
    if model.startswith("gpt"):
        estimated_tokens += 10  # Overhead for chat formatting
    
    return estimated_tokens


def truncate_text_to_tokens(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
    """Truncate text to fit within token limit"""
    current_tokens = estimate_token_count(text, model)
    
    if current_tokens <= max_tokens:
        return text
    
    # Calculate how much to truncate
    ratio = max_tokens / current_tokens
    target_chars = int(len(text) * ratio * 0.9)  # Leave some buffer
    
    # Truncate and add ellipsis
    if target_chars < len(text):
        truncated = text[:target_chars].rsplit(' ', 1)[0]  # Don't cut words
        return truncated + "..."
    
    return text


def format_transcript_for_llm(transcripts: List[Dict]) -> str:
    """Format transcript data for LLM consumption"""
    formatted_lines = []
    
    for t in transcripts:
        timestamp = f"[{t['start_time']:.1f}s - {t['end_time']:.1f}s]"
        speaker = t.get('speaker_id', 'Unknown')
        text = t.get('text', '')
        
        formatted_lines.append(f"{timestamp} {speaker}: {text}")
    
    return "\n".join(formatted_lines)


def format_code_context_for_llm(code_context: Dict) -> str:
    """Format code context for LLM consumption"""
    sections = []
    
    if files := code_context.get('file_references'):
        sections.append(f"Files mentioned: {', '.join(files)}")
    
    if functions := code_context.get('functions_mentioned'):
        sections.append(f"Functions discussed: {', '.join(functions)}")
    
    if prs := code_context.get('pr_references'):
        sections.append(f"PR references: {', '.join(prs)}")
    
    if issues := code_context.get('issue_references'):
        sections.append(f"Issue references: {', '.join(issues)}")
    
    if code_snippets := code_context.get('code_snippets'):
        sections.append(f"Code snippets: {len(code_snippets)} found")
    
    return "\n".join(sections) if sections else "No code context available"
