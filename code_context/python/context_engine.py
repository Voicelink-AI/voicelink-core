"""
Code Context Engine for Voicelink - Recognizes code in transcripts
"""
import os
import sys
import re
from typing import List, Dict, Any
from pathlib import Path

try:
    # Add bindings path
    sys.path.insert(0, str(Path(__file__).parent.parent / "build" / "bindings" / "Release"))
    import code_parser_py
    CODE_PARSER_AVAILABLE = True
except ImportError:
    CODE_PARSER_AVAILABLE = False

class CodeContextEngine:
    """Engine to detect and analyze code context in meeting transcripts"""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path
        self.code_symbols = {}
        self.github_patterns = {
            'pr': re.compile(r'(?:pull request|PR)\s*#?(\d+)', re.IGNORECASE),
            'issue': re.compile(r'issue\s*#?(\d+)', re.IGNORECASE),
            'commit': re.compile(r'commit\s+([a-f0-9]{7,40})', re.IGNORECASE),
            'branch': re.compile(r'branch\s+([a-zA-Z0-9_\-/]+)', re.IGNORECASE),
        }
        
        if repo_path and CODE_PARSER_AVAILABLE:
            self._scan_repository()
        
        print(f"🔍 Code Context Engine initialized")
        print(f"  Repository: {repo_path or 'None'}")
        print(f"  C++ Parser: {'✅ Available' if CODE_PARSER_AVAILABLE else '❌ Not available'}")
    
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
    
    def _scan_repository(self):
        """Scan repository for code symbols using C++ parser"""
        if not CODE_PARSER_AVAILABLE or not self.repo_path:
            return
        
        parser = code_parser_py.CodeParser()
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'build']]
            
            for file in files:
                file_path = os.path.join(root, file)
                language = parser.detect_language(file_path)
                
                if language != "unknown":
                    try:
                        symbols = parser.scan_file(file_path)
                        for symbol in symbols:
                            if symbol.name not in self.code_symbols:
                                self.code_symbols[symbol.name] = []
                            
                            self.code_symbols[symbol.name].append({
                                "type": symbol.type,
                                "file": file_path,
                                "line": symbol.line,
                                "language": language
                            })
                    except Exception as e:
                        print(f"⚠️  Error scanning {file_path}: {e}")
        
        print(f"📚 Scanned repository: {len(self.code_symbols)} unique symbols found")
    
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
        
        return list(set(found_terms))  # Remove duplicates
    
    def _find_api_mentions(self, transcript: str) -> List[str]:
        """Find API endpoint mentions"""
        api_patterns = [
            r'/api/[\w/]+',
            r'https?://[\w\./\-]+/api',
            r'[\w]+\.[\w]+\(.*\)',  # Function calls
            r'GET|POST|PUT|DELETE|PATCH'  # HTTP methods
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
context_engine = None

def initialize_context_engine(repo_path: str = None):
    """Initialize the global context engine"""
    global context_engine
    context_engine = CodeContextEngine(repo_path)
    return context_engine

def analyze_transcript_context(transcript: str) -> Dict[str, Any]:
    """Analyze transcript for code context"""
    if context_engine is None:
        initialize_context_engine()
    
    return context_engine.analyze_transcript(transcript)
