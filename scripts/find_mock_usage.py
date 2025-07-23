"""
Find files in the Python backend that are using mock audio processing
"""
import os
import re
from pathlib import Path

def find_mock_usage():
    """Find Python files that mention mock audio processing"""
    
    search_patterns = [
        r'mock.*audio',
        r'audio.*mock', 
        r'MockAudio',
        r'mock_audio',
        r'# TODO.*audio',
        r'AUDIO_ENGINE_AVAILABLE.*False',
        r'use_mock',
    ]
    
    backend_dirs = ['api', 'llm_engine', 'persistence']
    found_files = []
    
    for backend_dir in backend_dirs:
        if not Path(backend_dir).exists():
            continue
            
        print(f"🔍 Searching in {backend_dir}/...")
        
        for root, dirs, files in os.walk(backend_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in search_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_files.append(str(file_path))
                                print(f"  📄 Found mock usage in: {file_path}")
                                break
                                
                    except Exception as e:
                        print(f"  ⚠️  Could not read {file_path}: {e}")
    
    if found_files:
        print(f"\n📊 Found {len(found_files)} files with potential mock audio usage:")
        for file_path in found_files:
            print(f"  - {file_path}")
    else:
        print("\n✅ No obvious mock audio usage found - backend may already be ready!")
    
    return found_files

if __name__ == "__main__":
    find_mock_usage()
