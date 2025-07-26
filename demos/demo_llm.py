"""
LLM Provider Demo

Demonstrates LLM adapter functionality with sample prompts.
"""

import asyncio
import os

async def demo_llm_adapters():
    """Demonstrate LLM adapter functionality"""
    
    print("🧠 LLM ADAPTERS DEMONSTRATION")
    print("=" * 50)
    
    # Test if OpenAI adapter is available
    try:
        from llm_engine.adapters import OpenAIAdapter, OPENAI_AVAILABLE
        print(f"OpenAI Adapter Available: {'✅ Yes' if OPENAI_AVAILABLE else '❌ No'}")
        
        if OPENAI_AVAILABLE:
            print("\n🔧 OpenAI Adapter Features:")
            print("  - Async batch processing")
            print("  - Cost estimation") 
            print("  - Multiple model support")
            print("  - Smart error handling")
            
            # Show available models
            adapter = OpenAIAdapter(api_key="dummy")  # Just for model list
            models = adapter.get_available_models()
            print(f"  - Available models: {', '.join(models[:3])}...")
            
    except Exception as e:
        print(f"OpenAI Adapter Error: {e}")
    
    # Test VertexAI adapter
    try:
        from llm_engine.adapters import VertexAIAdapter, VERTEXAI_AVAILABLE
        print(f"\nVertexAI Adapter Available: {'✅ Yes' if VERTEXAI_AVAILABLE else '❌ No'}")
        
        if VERTEXAI_AVAILABLE:
            print("\n🔧 VertexAI Adapter Features:")
            print("  - Google Cloud integration")
            print("  - Text-bison models")
            print("  - Parallel processing")
            print("  - Enterprise scaling")
            
    except Exception as e:
        print(f"VertexAI Adapter Error: {e}")
    
    # Show LLM pipeline configuration
    print(f"\n⚙️ CURRENT LLM CONFIGURATION")
    print("-" * 30)
    provider = os.getenv('LLM_PROVIDER', 'mock')
    print(f"Provider: {provider}")
    print(f"OpenAI Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"GCP Project: {'✅ Set' if os.getenv('GCP_PROJECT_ID') else '❌ Not set'}")
    
    # Show prompt library
    print(f"\n📚 PROMPT LIBRARY DEMO")
    print("-" * 30)
    
    from llm_engine.utils import PromptLibrary
    prompt_lib = PromptLibrary()
    
    sample_transcript = "Alice: Let's discuss the API redesign. Bob: I agree, we need better authentication."
    
    try:
        summary_prompt = prompt_lib.get_prompt("meeting_summary", 
                                               transcript=sample_transcript,
                                               participants=["Alice", "Bob"])
        print("✅ Meeting summary prompt generated")
        print(f"   Preview: {summary_prompt[:100]}...")
        
        action_prompt = prompt_lib.get_prompt("action_items", 
                                              transcript=sample_transcript)
        print("✅ Action items prompt generated") 
        print(f"   Preview: {action_prompt[:100]}...")
        
    except Exception as e:
        print(f"Prompt generation error: {e}")

if __name__ == "__main__":
    asyncio.run(demo_llm_adapters())
