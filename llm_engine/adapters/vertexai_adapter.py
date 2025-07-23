"""
Google VertexAI Adapter for LLM Pipeline

Implements the LLM adapter interface for Google's VertexAI models.
"""

import asyncio
from typing import Dict, List, Optional, Any
import logging
import json
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
import vertexai
from vertexai.language_models import TextGenerationModel
from ..utils import LLMMetrics

logger = logging.getLogger(__name__)


class VertexAIAdapter:
    """Google VertexAI adapter for LLM operations"""
    
    def __init__(
        self, 
        project_id: str,
        location: str = "us-central1",
        model_name: str = "text-bison@001"
    ):
        """
        Initialize VertexAI adapter
        
        Args:
            project_id: GCP project ID
            location: GCP location for VertexAI
            model_name: Model to use
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.metrics = LLMMetrics()
        
        # Initialize VertexAI
        vertexai.init(project=project_id, location=location)
        self.model = TextGenerationModel.from_pretrained(model_name)
        
        logger.info(f"VertexAI adapter initialized with model: {model_name}")
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response from VertexAI
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Estimate input tokens
            input_tokens = self.metrics.estimate_tokens(prompt)
            
            # Generate response
            response = self.model.predict(
                prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=kwargs.get('top_p', 0.95),
                top_k=kwargs.get('top_k', 40)
            )
            
            result = {
                "content": response.text,
                "model": self.model_name,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": self.metrics.estimate_tokens(response.text),
                    "total_tokens": input_tokens + self.metrics.estimate_tokens(response.text)
                },
                "finish_reason": "stop"  # VertexAI doesn't provide finish reason
            }
            
            logger.info(f"VertexAI response generated: {result['usage']['total_tokens']} tokens")
            return result
            
        except Exception as e:
            logger.error(f"VertexAI API error: {e}")
            raise
    
    async def generate_batch_responses(
        self,
        prompts: List[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple responses in parallel
        """
        # VertexAI predict is not async, so we run in executor
        loop = asyncio.get_event_loop()
        
        async def generate_single(prompt):
            return await loop.run_in_executor(
                None, 
                lambda: asyncio.create_task(
                    self.generate_response(prompt, temperature, max_tokens, **kwargs)
                ).result()
            )
        
        tasks = [generate_single(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing prompt {i}: {result}")
                processed_results.append({
                    "content": f"Error: {str(result)}",
                    "error": True,
                    "model": self.model_name
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def generate_summary(
        self,
        text: str,
        summary_type: str = "comprehensive",
        max_length: int = 500
    ) -> str:
        """Generate summary of given text"""
        prompt_templates = {
            "comprehensive": f"""Provide a comprehensive summary of the following text in approximately {max_length} words:

{text}

Summary:""",
            "brief": f"""Provide a brief summary of the following text in approximately {max_length//2} words:

{text}

Brief Summary:""",
            "bullet_points": f"""Summarize the following text as bullet points (max {max_length} words total):

{text}

Key Points:
•"""
        }
        
        prompt = prompt_templates.get(summary_type, prompt_templates["comprehensive"])
        
        response = await self.generate_response(
            prompt,
            temperature=0.5,
            max_tokens=min(max_length * 2, 1500)
        )
        
        return response["content"]
    
    async def extract_action_items(self, text: str) -> List[Dict[str, str]]:
        """Extract action items from text"""
        prompt = f"""Extract action items from the following text. Format as JSON array with objects containing 'task', 'assignee' (if mentioned), and 'priority' (high/medium/low):

{text}

Action Items (JSON format):"""
        
        response = await self.generate_response(
            prompt,
            temperature=0.3,
            max_tokens=800
        )
        
        try:
            content = response["content"].strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            action_items = json.loads(content)
            return action_items if isinstance(action_items, list) else [action_items]
            
        except json.JSONDecodeError:
            logger.warning("Could not parse action items as JSON, returning raw text")
            return [{"task": response["content"], "assignee": "Unknown", "priority": "medium"}]
    
    async def analyze_code_context(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code context and generate documentation"""
        prompt = f"""Analyze the following {language} code and provide:
1. Brief description of what the code does
2. Key functions/classes and their purposes
3. Dependencies and imports
4. Potential issues or improvements
5. Documentation suggestions

Code:
```{language}
{code}
```

Analysis (JSON format):"""
        
        response = await self.generate_response(
            prompt,
            temperature=0.4,
            max_tokens=1200
        )
        
        try:
            content = response["content"].strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            return {
                "description": response["content"],
                "functions": [],
                "dependencies": [],
                "issues": [],
                "documentation": response["content"]
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available VertexAI models"""
        return [
            "text-bison@001",
            "text-bison@002", 
            "text-bison-32k@002",
            "chat-bison@001",
            "chat-bison@002",
            "chat-bison-32k@002"
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost based on token usage"""
        # VertexAI Text Generation pricing (as of 2024)
        input_cost_per_1k = 0.001
        output_cost_per_1k = 0.001
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
