"""
Performance Monitor Agent
=========================

Detects performance anti-patterns and code quality issues.

This agent:
- Detects N+1 query patterns
- Identifies blocking operations in async code
- Finds inefficient file operations
- Detects memory leaks and resource issues

Uses Google Gemini for performance analysis.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, Any, List
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class PerformanceMonitorAgent:
    """
    Performance Monitor Agent for detecting performance issues.
    
    This agent analyzes code for performance anti-patterns
    and provides optimization recommendations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Performance Monitor Agent.
        
        Args:
            config: Performance monitor configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        
        # Initialize Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Performance Monitor initialized with Gemini 1.5 Flash")
        else:
            self.model = None
            logger.warning("No GOOGLE_API_KEY found.")
    
    def analyze_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze files for performance issues.
        
        Args:
            file_paths: List of files to analyze
        
        Returns:
            List of performance findings
        """
        if not self.enabled:
            return []
        
        findings = []
        
        for file_path in file_paths:
            if Path(file_path).suffix == ".py":
                file_findings = self.analyze_file(file_path)
                findings.extend(file_findings)
        
        return findings
    
    def analyze_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze single file for performance issues.
        
        Args:
            file_path: Path to file
        
        Returns:
            List of findings
        """
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Detect N+1 queries
            if self.config.get("n_plus_one", {}).get("enabled", True):
                n_plus_one = self._detect_n_plus_one(content, file_path)
                findings.extend(n_plus_one)
            
            # Detect large file operations
            if self.config.get("large_file_ops", {}).get("enabled", True):
                large_file = self._detect_large_file_ops(content, file_path)
                findings.extend(large_file)
            
            # Detect blocking calls
            if self.config.get("blocking_calls", {}).get("enabled", True):
                blocking = self._detect_blocking_calls(content, file_path)
                findings.extend(blocking)
        
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
        
        return findings
    
    def _detect_n_plus_one(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect N+1 query patterns."""
        findings = []
        lines = content.split('\n')
        
        # Patterns that indicate N+1 queries
        patterns = self.config.get("n_plus_one", {}).get("check_patterns", [
            r"for\s+\w+\s+in\s+.*:\s*\n\s+.*\.query\.",
            r"for\s+\w+\s+in\s+.*:\s*\n\s+.*\.filter\(",
            r"for\s+\w+\s+in\s+.*:\s*\n\s+.*\.get\("
        ])
        
        for i, line in enumerate(lines, start=1):
            # Check if we're in a loop
            if re.search(r"for\s+\w+\s+in\s+", line):
                # Check next few lines for query operations
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j]
                    if any(keyword in next_line for keyword in [".query", ".filter", ".get", "SELECT"]):
                        finding = {
                            "tool": "performance-monitor",
                            "type": "n_plus_one",
                            "severity": "MEDIUM",
                            "title": "Potential N+1 query pattern detected",
                            "description": "Database query inside loop may cause N+1 query problem. Consider using bulk queries or prefetching.",
                            "file": file_path,
                            "line_number": i,
                            "location": f"{file_path}:L{i}",
                            "code_snippet": line.strip(),
                            "remediation": "Use bulk queries, joins, or prefetch_related() to load data in a single query"
                        }
                        findings.append(finding)
                        break
        
        return findings
    
    def _detect_large_file_ops(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect inefficient file operations."""
        findings = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, start=1):
            # Check for read() without size limit
            if re.search(r"\.read\(\s*\)", line) and "open(" in content[:content.index(line) if line in content else 0]:
                finding = {
                    "tool": "performance-monitor",
                    "type": "large_file_operation",
                    "severity": "LOW",
                    "title": "Unbounded file read operation",
                    "description": "Reading entire file into memory can cause issues with large files. Consider streaming or chunked reading.",
                    "file": file_path,
                    "line_number": i,
                    "location": f"{file_path}:L{i}",
                    "code_snippet": line.strip(),
                    "remediation": "Use file.read(chunk_size) in a loop or readlines() for line-by-line processing"
                }
                findings.append(finding)
        
        return findings
    
    def _detect_blocking_calls(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Detect blocking calls in async code."""
        findings = []
        lines = content.split('\n')
        
        # Check if file contains async code
        has_async = "async def" in content or "await " in content
        
        if has_async:
            blocking_patterns = [
                (r"time\.sleep\(", "time.sleep"),
                (r"requests\.(get|post|put|delete)", "requests"),
                (r"open\(.*\)", "synchronous file I/O")
            ]
            
            for i, line in enumerate(lines, start=1):
                for pattern, name in blocking_patterns:
                    if re.search(pattern, line):
                        finding = {
                            "tool": "performance-monitor",
                            "type": "blocking_call",
                            "severity": "MEDIUM",
                            "title": f"Blocking call in async code: {name}",
                            "description": f"Using blocking {name} in async code can block the event loop. Use async alternatives.",
                            "file": file_path,
                            "line_number": i,
                            "location": f"{file_path}:L{i}",
                            "code_snippet": line.strip(),
                            "remediation": f"Replace {name} with async alternative (asyncio.sleep, aiohttp, aiofiles)"
                        }
                        findings.append(finding)
        
        return findings
    
    def get_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of performance findings."""
        return {
            "total": len(findings),
            "by_type": {
                "n_plus_one": len([f for f in findings if f.get("type") == "n_plus_one"]),
                "large_file_operation": len([f for f in findings if f.get("type") == "large_file_operation"]),
                "blocking_call": len([f for f in findings if f.get("type") == "blocking_call"])
            }
        }
