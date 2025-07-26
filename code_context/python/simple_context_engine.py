"""
Simple Code Context Engine - Pure Python fallback
"""
import os
import re
from typing import List, Dict, Any
from pathlib import Path

class SimpleCodeContextEngine:
    """Pure Python code context engine as fallback"""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path
        self.code_symbols = {}
        self.github_patterns = {
            'pr': re.compile(r'(?:pull request|PR)\s*#?(\d+)', re.IGNORECASE),
            'issue': re.compile(r'issue\s*#?(\d+)', re.IGNORECASE),
            'commit': re.compile(r'commit\s+([a-f0-9]{7,40})', re.IGNORECASE),
            'branch': re.compile(r'branch\s+([a-zA-Z0-9_\-/]+)', re.IGNORECASE),
        }
        
        if repo_path:
            self._scan_repository_python()
        
        print(f"🔍 Simple Code Context Engine initialized (Pure Python)")
        print(f"  Repository: {repo_path or 'None'}")
    
    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """Analyze a transcript for code context"""
        context = {
            "code_references": [],
            "github_references": [],
            "technical_terms": [],
            "api_mentions": [],
            "file_mentions": []
        }
        
        # Find code symbols mentioned in transcript
        if self.code_symbols:
            context["code_references"] = self._find_code_references(transcript)
        
        # Find GitHub references (PRs, issues, commits)
        context["github_references"] = self._find_github_references(transcript)
        
        # Find technical terms and patterns
        context["technical_terms"] = self._find_technical_terms(transcript)
        
        # Find API and file mentions
        context["api_mentions"] = self._find_api_mentions(transcript)
        context["file_mentions"] = self._find_file_mentions(transcript)
        
        return context
    
    def _scan_repository_python(self):
        """Scan repository using pure Python parsing"""
        if not self.repo_path:
            return
        
        print("📚 Scanning repository with Python parser...")
        
        # File patterns to look for
        code_extensions = {'.py', '.cpp', '.c', '.h', '.hpp', '.js', '.ts', '.java', '.go', '.rs'}
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'build', '.vscode']]
            
            for file in files:
                file_path = Path(root) / file
                
                if file_path.suffix.lower() in code_extensions:
                    try:
                        self._scan_file_python(str(file_path))
                    except Exception as e:
                        print(f"⚠️  Error scanning {file_path}: {e}")
        
        print(f"📚 Scanned repository: {len(self.code_symbols)} unique symbols found")
    
    def _scan_file_python(self, file_path: str):
        """Scan a single file for code symbols using Python regex"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                
            language = self._detect_language(file_path)
            
            # Language-specific patterns
            patterns = []
            if language == "python":
                patterns = [
                    (r'^def\s+(\w+)\s*\(', 'function'),
                    (r'^class\s+(\w+)\s*[:(\(]', 'class'),
                    (r'^(\w+)\s*=', 'variable'),
                    (r'import\s+(\w+)', 'import'),
                    (r'from\s+(\w+)\s+import', 'import'),
                ]
            elif language in ["cpp", "c"]:
                patterns = [
                    (r'^\s*\w+\s+(\w+)\s*\([^)]*\)\s*\{', 'function'),
                    (r'^\s*class\s+(\w+)', 'class'),
                    (r'^\s*struct\s+(\w+)', 'struct'),
                    (r'#include\s*[<"]([^>"]+)[>"]', 'include'),
                ]
            elif language in ["javascript", "typescript"]:
                patterns = [
                    (r'function\s+(\w+)\s*\(', 'function'),
                    (r'const\s+(\w+)\s*=', 'constant'),
                    (r'class\s+(\w+)', 'class'),
                    (r'import.*from\s+[\'"]([^\'"]+)[\'"]+', 'import'),
                ]
            
            # Scan each line
            for line_num, line in enumerate(lines, 1):
                for pattern, symbol_type in patterns:
                    match = re.search(pattern, line)
                    if match:
                        symbol_name = match.group(1)
                        
                        if symbol_name not in self.code_symbols:
                            self.code_symbols[symbol_name] = []
                        
                        self.code_symbols[symbol_name].append({
                            "type": symbol_type,
                            "file": file_path,
                            "line": line_num,
                            "language": language
                        })
                        
        except Exception as e:
            # Skip files that can't be read
            pass
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extension = Path(file_path).suffix.lower()
        
        lang_map = {
            '.py': 'python',
            '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'header', '.hpp': 'header',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        return lang_map.get(extension, 'unknown')
    
    def _find_code_references(self, transcript: str) -> List[Dict[str, Any]]:
        """Find references to code symbols in transcript"""
        references = []
        words = re.findall(r'\b\w+\b', transcript.lower())
        
        for word in words:
            if word in self.code_symbols:
                for symbol_info in self.code_symbols[word]:
                    references.append({
                        "symbol": word,
                        "type": symbol_info["type"],
                        "file": symbol_info["file"],
                        "line": symbol_info["line"],
                        "language": symbol_info["language"],
                        "context": "mentioned in transcript"
                    })
        
        return references
    
    def _find_github_references(self, transcript: str) -> List[Dict[str, Any]]:
        """Find GitHub-related references (PRs, issues, commits)"""
        references = []
        
        for ref_type, pattern in self.github_patterns.items():
            matches = pattern.finditer(transcript)
            for match in matches:
                references.append({
                    "type": ref_type,
                    "value": match.group(1),
                    "full_match": match.group(0),
                    "position": match.span()
                })
        
        return references
    
    def _find_technical_terms(self, transcript: str) -> List[str]:
        """Find technical programming terms"""
        tech_terms = [
            'api', 'database', 'backend', 'frontend', 'microservice', 'docker',
            'kubernetes', 'deployment', 'authentication', 'authorization',
            'endpoint', 'middleware', 'framework', 'library', 'repository',
            'function', 'class', 'method', 'variable', 'algorithm', 'architecture',
            'pipeline', 'webhook', 'rest', 'graphql', 'json', 'xml', 'yaml',
            'testing', 'debugging', 'refactoring', 'optimization', 'performance'
        ]
        
        found_terms = []
        transcript_lower = transcript.lower()
        
        for term in tech_terms:
            if term in transcript_lower:
                found_terms.append(term)
        
        return list(set(found_terms))
    
    def _find_api_mentions(self, transcript: str) -> List[str]:
        """Find API endpoint mentions"""
        api_patterns = [
            r'/api/[\w/]+',
            r'https?://[\w\./\-]+/api',
            r'[\w]+\.[\w]+\(.*\)',
            r'GET|POST|PUT|DELETE|PATCH'
        ]
        
        mentions = []
        for pattern in api_patterns:
            matches = re.finditer(pattern, transcript, re.IGNORECASE)
            for match in matches:
                mentions.append(match.group(0))
        
        return list(set(mentions))
    
    def _find_file_mentions(self, transcript: str) -> List[str]:
        """Find file path mentions"""
        file_pattern = r'[\w/\-\.]+\.(?:py|js|ts|cpp|c|h|java|go|rs|md|json|yaml|yml|txt)'
        
        matches = re.finditer(file_pattern, transcript, re.IGNORECASE)
        return [match.group(0) for match in matches]

# Global instance
simple_context_engine = None

def initialize_simple_context_engine(repo_path: str = None):
    """Initialize the simple context engine"""
    global simple_context_engine
    simple_context_engine = SimpleCodeContextEngine(repo_path)
    return simple_context_engine

def analyze_transcript_simple(transcript: str) -> Dict[str, Any]:
    """Analyze transcript for code context using simple engine"""
    if simple_context_engine is None:
        initialize_simple_context_engine()
    
    return simple_context_engine.analyze_transcript(transcript)
