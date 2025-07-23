"""
Development server runner for VoiceLink Core
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run the development server"""
    print("🚀 Starting VoiceLink Core Development Server...")
    print(f"📁 Project root: {project_root}")
    
    # Check if audio engine is deployed
    audio_engine_file = project_root / "audio_engine_py.cp313-win_amd64.pyd"
    if audio_engine_file.exists():
        print("✅ Audio engine found")
    else:
        print("⚠️  Audio engine not found - run deploy_audio_engine.py first")
    
    # Run the server
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root)],
        log_level="info"
    )

if __name__ == "__main__":
    main()
