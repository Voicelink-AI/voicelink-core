"""
LLM Engine Adapters

This package contains adapters for different LLM providers.
"""

try:
    from .openai_adapter import OpenAIAdapter
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIAdapter = None

try:
    from .vertexai_adapter import VertexAIAdapter
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    VertexAIAdapter = None

__all__ = []

if OPENAI_AVAILABLE:
    __all__.append("OpenAIAdapter")

if VERTEXAI_AVAILABLE:
    __all__.append("VertexAIAdapter")
