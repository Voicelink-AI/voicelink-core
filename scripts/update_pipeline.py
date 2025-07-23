"""
Update the LLM pipeline to use the real audio engine
"""
import sys
from pathlib import Path
import shutil

def update_pipeline():
    """Update the pipeline file to use real audio engine"""
    
    pipeline_file = Path("llm_engine/pipeline.py")
    backup_file = Path("llm_engine/pipeline.py.backup")
    
    if not pipeline_file.exists():
        print(f"❌ File not found: {pipeline_file}")
        return False
    
    # Create backup
    shutil.copy2(pipeline_file, backup_file)
    print(f"💾 Backup created: {backup_file}")
    
    try:
        with open(pipeline_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace mock imports with real audio bridge import
        content = content.replace(
            "# Mock audio processing imports", 
            "# Real audio processing imports\nfrom audio_bridge import load_audio, detect_voice_segments, diarize_speakers, get_audio_info"
        )
        
        # Replace any mock audio calls with real ones
        replacements = [
            ("mock_audio_processor", "load_audio"),
            ("mock_detect_voice", "detect_voice_segments"),
            ("mock_diarize", "diarize_speakers"),
            ("use_mock_audio = True", "use_mock_audio = False"),
            ("AUDIO_ENGINE_AVAILABLE = False", "AUDIO_ENGINE_AVAILABLE = True"),
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
        
        # Write updated content
        with open(pipeline_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated: {pipeline_file}")
        print("🔧 Changes made:")
        print("  - Replaced mock imports with real audio bridge")
        print("  - Updated function calls to use real audio engine")
        print("  - Set AUDIO_ENGINE_AVAILABLE = True")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating file: {e}")
        # Restore backup on error
        shutil.copy2(backup_file, pipeline_file)
        print(f"🔄 Restored backup due to error")
        return False

if __name__ == "__main__":
    update_pipeline()
