"""
Deploy the compiled C++ audio engine to the Python backend
"""
import shutil
import os
from pathlib import Path

def deploy_audio_engine():
    """Copy the compiled audio engine to where Python backend expects it"""
    
    # Source: Your compiled audio engine
    source_file = Path(__file__).parent.parent / "audio_engine" / "build" / "bindings" / "Release" / "audio_engine_py.cp313-win_amd64.pyd"
    
    # Common deployment locations for the Python backend
    deployment_targets = [
        Path(__file__).parent.parent / "api",
        Path(__file__).parent.parent / "llm_engine", 
        Path(__file__).parent.parent / "persistence",
        Path(__file__).parent.parent,  # Root directory
    ]
    
    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return False
    
    print(f"📁 Source: {source_file}")
    
    deployed = False
    for target_dir in deployment_targets:
        if target_dir.exists():
            target_file = target_dir / source_file.name
            try:
                shutil.copy2(source_file, target_file)
                print(f"✅ Deployed to: {target_file}")
                deployed = True
            except Exception as e:
                print(f"❌ Failed to deploy to {target_file}: {e}")
    
    if deployed:
        print("🎉 Audio engine deployed successfully!")
        print("Next: Update Python imports to use the real audio engine")
    else:
        print("❌ No valid deployment targets found")
    
    return deployed

if __name__ == "__main__":
    deploy_audio_engine()
