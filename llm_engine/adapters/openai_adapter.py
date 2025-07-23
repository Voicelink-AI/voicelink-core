"""
OpenAI API Adapter for LLM Pipeline

Implements the LLM adapter interface for OpenAI's GPT models.
"""

import asyncio
import openai
from typing import Dict, List, Optional, Any
import logging
from ..utils import LLMMetrics

logger = logging.getLogger(__name__)


class OpenAIAdapter:
    """OpenAI API adapter for LLM operations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI adapter
        
        Args:
            api_key: OpenAI API key (if None, will use environment variable)
            model: Model to use (default: gpt-4)
        """
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.metrics = LLMMetrics()
        logger.info(f"OpenAI adapter initialized with model: {model}")
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response from OpenAI API
        
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
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Extract response
            content = response.choices[0].message.content
            usage = response.usage
            
            result = {
                "content": content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(f"OpenAI response generated: {usage.total_tokens} tokens")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
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
        
        Args:
            prompts: List of input prompts
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            **kwargs: Additional parameters
            
        Returns:
            List of response dictionaries
        """
        tasks = [
            self.generate_response(prompt, temperature, max_tokens, **kwargs)
            for prompt in prompts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing prompt {i}: {result}")
                processed_results.append({
                    "content": f"Error: {str(result)}",
                    "error": True,
                    "model": self.model
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
        """
        Generate summary of given text
        
        Args:
            text: Text to summarize
            summary_type: Type of summary (comprehensive, brief, bullet_points)
            max_length: Maximum length of summary
            
        Returns:
            Generated summary
        """
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
        """
        Extract action items from text
        
        Args:
            text: Input text
            
        Returns:
            List of action items with assignee and due date info
        """
        prompt = f"""Extract action items from the following text. Format as JSON array with objects containing 'task', 'assignee' (if mentioned), and 'priority' (high/medium/low):

{text}

Action Items (JSON format):"""
        
        response = await self.generate_response(
            prompt,
            temperature=0.3,
            max_tokens=800
        )
        
        try:
            import json
            # Try to parse JSON response
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
        """
        Analyze code context and generate documentation
        
        Args:
            code: Source code to analyze
            language: Programming language
            
        Returns:
            Analysis results
        """
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
            import json
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
        """Get list of available OpenAI models"""
        return [
            "gpt-4",
            "gpt-4-1106-preview",
            "gpt-4-0613",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-1106",
            "gpt-3.5-turbo-16k"
        ]
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate API cost based on token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # GPT-4 pricing (as of 2024)
        if "gpt-4" in self.model:
            input_cost_per_1k = 0.03
            output_cost_per_1k = 0.06
        else:  # GPT-3.5 pricing
            input_cost_per_1k = 0.0015
            output_cost_per_1k = 0.002
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
