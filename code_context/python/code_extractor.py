"""
Code Context Python Wrapper

Python interface for the C++ code parsing and context extraction engine.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class CodeContextExtractor:
    """
    Python wrapper for C++ code context engine
    """
    
    def __init__(self):
        self.initialized = False
        self._init_code_engine()
    
    def _init_code_engine(self):
        """Initialize the C++ code context engine"""
        try:
            # This would import the actual C++ binding
            # import code_context_py
            # self.engine = code_context_py.CodeParser()
            logger.info("Code context engine initialized (mock mode)")
            self.initialized = True
        except ImportError as e:
            logger.warning(f"C++ code context engine not available: {e}")
            logger.info("Running in mock mode")
            self.initialized = False
    
    def extract_code_context(self, transcripts: List[Dict]) -> Dict[str, Any]:
        """
        Extract code context from meeting transcripts
        
        Args:
            transcripts: List of transcript segments
            
        Returns:
            Code context including files, functions, PRs, issues mentioned
        """
        try:
            if self.initialized:
                # Actual C++ call would be:
                # return self.engine.extract_context(transcripts)
                pass
            
            # Mock extraction using simple regex patterns
            logger.info("Extracting code context from transcripts")
            
            combined_text = " ".join([t.get('text', '') for t in transcripts])
            
            context = {
                "file_references": self._extract_file_references(combined_text),
                "function_references": self._extract_function_references(combined_text),
                "pr_references": self._extract_pr_references(combined_text),
                "issue_references": self._extract_issue_references(combined_text),
                "code_snippets": self._extract_code_snippets(combined_text),
                "technical_terms": self._extract_technical_terms(combined_text)
            }
            
            logger.info(f"Extracted: {len(context['file_references'])} files, "
                       f"{len(context['pr_references'])} PRs, "
                       f"{len(context['issue_references'])} issues")
            
            return context
            
        except Exception as e:
            logger.error(f"Code context extraction failed: {e}")
            raise
    
    def _extract_file_references(self, text: str) -> List[str]:
        """Extract file references from text"""
        # Common file patterns
        patterns = [
            r'\b\w+\.py\b',          # Python files
            r'\b\w+\.js\b',          # JavaScript files
            r'\b\w+\.ts\b',          # TypeScript files
            r'\b\w+\.cpp\b',         # C++ files
            r'\b\w+\.h\b',           # Header files
            r'\b\w+\.json\b',        # JSON files
            r'\b\w+\.yml\b',         # YAML files
            r'\b\w+\.yaml\b',        # YAML files
        ]
        
        files = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            files.update(matches)
        
        return list(files)
    
    def _extract_function_references(self, text: str) -> List[str]:
        """Extract function/method references from text"""
        # Common function patterns
        patterns = [
            r'\b\w+\(\)',            # function()
            r'\b\w+\s*\(\s*\w+',     # function(param
            r'\bdef\s+(\w+)',        # def function_name
            r'\bfunction\s+(\w+)',   # function function_name
            r'\b(\w+)\.(\w+)\(',     # object.method(
        ]
        
        functions = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches[0] if matches else None, tuple):
                functions.update([match[0] for match in matches if match])
            else:
                functions.update(matches)
        
        return list(functions)
    
    def _extract_pr_references(self, text: str) -> List[str]:
        """Extract pull request references from text"""
        patterns = [
            r'\bPR\s*#?(\d+)\b',     # PR #123 or PR123
            r'\bpull\s+request\s*#?(\d+)\b',  # pull request #123
            r'#(\d+)',               # #123 (generic)
        ]
        
        prs = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            prs.update([f"#{match}" for match in matches])
        
        return list(prs)
    
    def _extract_issue_references(self, text: str) -> List[str]:
        """Extract issue references from text"""
        patterns = [
            r'\bissue\s*#?(\d+)\b',  # issue #123
            r'\bbug\s*#?(\d+)\b',    # bug #123
            r'\bticket\s*#?(\d+)\b', # ticket #123
        ]
        
        issues = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            issues.update([f"#{match}" for match in matches])
        
        return list(issues)
    
    def _extract_code_snippets(self, text: str) -> List[Dict[str, str]]:
        """Extract potential code snippets from text"""
        # Look for code-like patterns
        snippets = []
        
        # Find text within backticks
        backtick_pattern = r'`([^`]+)`'
        matches = re.findall(backtick_pattern, text)
        
        for match in matches:
            if any(keyword in match.lower() for keyword in 
                  ['def ', 'function', 'class ', 'import ', 'from ', 'const ', 'let ', 'var ']):
                snippets.append({
                    "content": match,
                    "language": "unknown",
                    "type": "inline"
                })
        
        return snippets
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms and technologies mentioned"""
        # Common technical terms
        tech_terms = [
            'api', 'rest', 'graphql', 'database', 'sql', 'nosql',
            'docker', 'kubernetes', 'aws', 'gcp', 'azure',
            'react', 'angular', 'vue', 'node', 'express',
            'python', 'javascript', 'typescript', 'java', 'c++',
            'microservice', 'authentication', 'authorization',
            'jwt', 'oauth', 'saml', 'ssl', 'tls', 'https',
            'redis', 'postgres', 'mysql', 'mongodb',
            'git', 'github', 'gitlab', 'bitbucket',
            'ci', 'cd', 'pipeline', 'deployment'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in tech_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms


class RepositoryAnalyzer:
    """
    Analyzes repository structure and connects transcript context to actual code
    """
    
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path
        self.code_extractor = CodeContextExtractor()
    
    def analyze_repository_context(self, 
                                 code_context: Dict[str, Any],
                                 repo_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Analyze repository to validate and enhance code context
        
        Args:
            code_context: Extracted code context from transcripts
            repo_path: Path to repository (optional)
            
        Returns:
            Enhanced code context with repository information
        """
        try:
            working_repo = repo_path or self.repo_path
            
            if not working_repo or not working_repo.exists():
                logger.warning("Repository path not available, using transcript context only")
                return code_context
            
            logger.info(f"Analyzing repository at {working_repo}")
            
            # Validate file references against actual repository
            valid_files = self._validate_file_references(
                code_context.get('file_references', []),
                working_repo
            )
            
            # Find additional related files
            related_files = self._find_related_files(valid_files, working_repo)
            
            # Analyze code structure
            code_structure = self._analyze_code_structure(valid_files, working_repo)
            
            enhanced_context = {
                **code_context,
                "validated_files": valid_files,
                "related_files": related_files,
                "code_structure": code_structure,
                "repository_path": str(working_repo),
                "analysis_timestamp": logger.info("Repository analysis completed")
            }
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Repository analysis failed: {e}")
            return code_context
    
    def _validate_file_references(self, file_refs: List[str], repo_path: Path) -> List[str]:
        """Validate that referenced files actually exist in the repository"""
        valid_files = []
        
        for file_ref in file_refs:
            # Search for file in repository
            matches = list(repo_path.rglob(file_ref))
            if matches:
                valid_files.extend([str(match.relative_to(repo_path)) for match in matches])
            else:
                logger.warning(f"File {file_ref} not found in repository")
        
        return valid_files
    
    def _find_related_files(self, files: List[str], repo_path: Path) -> List[str]:
        """Find files related to the mentioned files"""
        related = []
        
        for file_path in files:
            full_path = repo_path / file_path
            if full_path.exists():
                # Find files in same directory
                parent_dir = full_path.parent
                siblings = [f for f in parent_dir.iterdir() 
                           if f.is_file() and f.suffix in ['.py', '.js', '.ts', '.cpp', '.h']]
                
                related.extend([str(s.relative_to(repo_path)) for s in siblings[:3]])
        
        return list(set(related))
    
    def _analyze_code_structure(self, files: List[str], repo_path: Path) -> Dict[str, Any]:
        """Analyze code structure of mentioned files"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "dependencies": []
        }
        
        for file_path in files[:5]:  # Limit analysis to first 5 files
            full_path = repo_path / file_path
            if full_path.exists() and full_path.suffix == '.py':
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Extract classes
                        classes = re.findall(r'class\s+(\w+)', content)
                        structure['classes'].extend(classes)
                        
                        # Extract functions
                        functions = re.findall(r'def\s+(\w+)', content)
                        structure['functions'].extend(functions)
                        
                        # Extract imports
                        imports = re.findall(r'(?:from|import)\s+(\w+)', content)
                        structure['imports'].extend(imports)
                        
                except Exception as e:
                    logger.warning(f"Could not analyze {file_path}: {e}")
        
        return structure
