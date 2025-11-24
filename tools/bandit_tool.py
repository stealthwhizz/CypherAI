"""
Bandit Tool Wrapper
===================

Wrapper for Bandit SAST (Static Application Security Testing) scanner.

Bandit is a tool designed to find common security issues in Python code.
It scans for patterns like SQL injection, command injection, hardcoded passwords, etc.

Documentation: https://bandit.readthedocs.io/
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BanditTool:
    """
    Wrapper for Bandit security scanner.
    
    This class provides methods to run Bandit scans on Python files
    and parse the results into a standardized format.
    """
    
    # Severity mapping from Bandit to Cypher AI
    SEVERITY_MAP = {
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW"
    }
    
    # Confidence mapping
    CONFIDENCE_MAP = {
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW"
    }
    
    def __init__(
        self,
        confidence_threshold: str = "LOW",
        severity_threshold: str = "LOW",
        exclude_tests: Optional[List[str]] = None
    ):
        """
        Initialize Bandit tool wrapper.
        
        Args:
            confidence_threshold: Minimum confidence level (LOW, MEDIUM, HIGH)
            severity_threshold: Minimum severity level (LOW, MEDIUM, HIGH)
            exclude_tests: List of Bandit test IDs to exclude (e.g., ['B201', 'B301'])
        """
        self.confidence_threshold = confidence_threshold
        self.severity_threshold = severity_threshold
        self.exclude_tests = exclude_tests or []
        
        # Check if Bandit is installed
        if not self._check_installed():
            logger.warning("Bandit is not installed. Install with: pip install bandit")
    
    def _check_installed(self) -> bool:
        """
        Check if Bandit is installed.
        
        Returns:
            True if Bandit is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Run Bandit scan on a single file.
        
        Args:
            file_path: Path to the Python file to scan
        
        Returns:
            List of findings with standardized structure
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a Python file
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix != ".py":
            logger.info(f"Skipping non-Python file: {file_path}")
            return []
        
        if not self._check_installed():
            logger.error("Bandit is not installed")
            return []
        
        try:
            # Create temporary file for JSON output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                output_file = tmp.name
            
            # Build Bandit command
            cmd = [
                "bandit",
                "-f", "json",
                "-o", output_file,
                "-ll",  # Report only findings with at least LOW severity
            ]
            
            # Add exclude tests if specified
            if self.exclude_tests:
                cmd.extend(["-s", ",".join(self.exclude_tests)])
            
            cmd.append(str(path))
            
            # Run Bandit
            logger.info(f"Running Bandit on {file_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse results
            findings = self._parse_results(output_file, file_path)
            
            # Clean up temporary file
            Path(output_file).unlink(missing_ok=True)
            
            logger.info(f"Bandit found {len(findings)} issue(s) in {file_path}")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error(f"Bandit scan timed out for {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error running Bandit on {file_path}: {e}")
            return []
    
    def scan_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """
        Run Bandit scan on all Python files in a directory.
        
        Args:
            dir_path: Path to the directory to scan
        
        Returns:
            List of findings from all files
        """
        path = Path(dir_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        
        if not path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")
        
        all_findings = []
        
        # Find all Python files
        python_files = list(path.rglob("*.py"))
        
        logger.info(f"Found {len(python_files)} Python file(s) in {dir_path}")
        
        for py_file in python_files:
            try:
                findings = self.scan_file(str(py_file))
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Error scanning {py_file}: {e}")
                continue
        
        return all_findings
    
    def _parse_results(self, output_file: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Parse Bandit JSON output into standardized format.
        
        Args:
            output_file: Path to Bandit JSON output file
            source_file: Path to the source file that was scanned
        
        Returns:
            List of standardized findings
        """
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error reading Bandit output: {e}")
            return []
        
        findings = []
        results = data.get("results", [])
        
        for result in results:
            finding = {
                "tool": "bandit",
                "severity": self._map_severity(result.get("issue_severity", "LOW")),
                "confidence": result.get("issue_confidence", "MEDIUM"),
                "title": result.get("issue_text", "Security issue detected"),
                "description": self._build_description(result),
                "file": source_file,
                "line_number": result.get("line_number", 0),
                "line_range": result.get("line_range", []),
                "code_snippet": result.get("code", ""),
                "cwe": self._extract_cwe(result),
                "test_id": result.get("test_id", ""),
                "test_name": result.get("test_name", ""),
                "more_info": result.get("more_info", ""),
                "location": f"{source_file}:L{result.get('line_number', 0)}",
            }
            
            # Only include findings that meet thresholds
            if self._meets_threshold(finding):
                findings.append(finding)
        
        return findings
    
    def _map_severity(self, bandit_severity: str) -> str:
        """
        Map Bandit severity to standardized severity.
        
        Args:
            bandit_severity: Bandit severity level
        
        Returns:
            Standardized severity level
        """
        return self.SEVERITY_MAP.get(bandit_severity.upper(), "LOW")
    
    def _extract_cwe(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract CWE ID from Bandit result.
        
        Args:
            result: Bandit result dictionary
        
        Returns:
            CWE ID if found, None otherwise
        """
        # Bandit includes CWE in the more_info URL
        more_info = result.get("more_info", "")
        if "CWE" in more_info:
            # Extract CWE number from URL or text
            import re
            match = re.search(r'CWE-(\d+)', more_info)
            if match:
                return f"CWE-{match.group(1)}"
        
        return None
    
    def _build_description(self, result: Dict[str, Any]) -> str:
        """
        Build detailed description from Bandit result.
        
        Args:
            result: Bandit result dictionary
        
        Returns:
            Detailed description string
        """
        issue_text = result.get("issue_text", "Security issue detected")
        test_name = result.get("test_name", "")
        
        description = f"{issue_text}"
        
        if test_name:
            description += f"\n\nTest: {test_name}"
        
        cwe = self._extract_cwe(result)
        if cwe:
            description += f"\n{cwe}"
        
        more_info = result.get("more_info", "")
        if more_info:
            description += f"\n\nMore info: {more_info}"
        
        return description
    
    def _meets_threshold(self, finding: Dict[str, Any]) -> bool:
        """
        Check if finding meets configured thresholds.
        
        Args:
            finding: Finding dictionary
        
        Returns:
            True if finding meets thresholds, False otherwise
        """
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        confidence_levels = ["LOW", "MEDIUM", "HIGH"]
        
        finding_severity = finding.get("severity", "LOW")
        finding_confidence = finding.get("confidence", "LOW")
        
        try:
            severity_met = (
                severity_levels.index(finding_severity) >= 
                severity_levels.index(self.severity_threshold)
            )
        except ValueError:
            severity_met = True
        
        try:
            confidence_met = (
                confidence_levels.index(finding_confidence) >= 
                confidence_levels.index(self.confidence_threshold)
            )
        except ValueError:
            confidence_met = True
        
        return severity_met and confidence_met
    
    def get_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for findings.
        
        Args:
            findings: List of findings
        
        Returns:
            Summary dictionary with counts and statistics
        """
        summary = {
            "total": len(findings),
            "by_severity": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            },
            "by_confidence": {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            },
            "unique_test_ids": set()
        }
        
        for finding in findings:
            severity = finding.get("severity", "LOW")
            confidence = finding.get("confidence", "LOW")
            test_id = finding.get("test_id", "")
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            if confidence in summary["by_confidence"]:
                summary["by_confidence"][confidence] += 1
            
            if test_id:
                summary["unique_test_ids"].add(test_id)
        
        summary["unique_test_ids"] = list(summary["unique_test_ids"])
        
        return summary
