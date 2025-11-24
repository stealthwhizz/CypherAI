"""
Security Scanner Agent
======================

Performs comprehensive security scanning using multiple tools.

This agent:
- Runs Bandit SAST scans on Python code
- Scans dependencies with Safety for known vulnerabilities
- Detects hardcoded secrets using regex patterns
- Optionally runs Trivy for container/IaC scanning
- Aggregates and normalizes findings

Uses Google Gemini for intelligent vulnerability analysis.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import google.generativeai as genai

from tools.bandit_tool import BanditTool
from tools.safety_tool import SafetyTool
from tools.trivy_tool import TrivyTool

logger = logging.getLogger(__name__)


class SecurityScannerAgent:
    """
    Security Scanner Agent for vulnerability detection.
    
    This agent coordinates multiple security scanning tools and
    uses Gemini for intelligent analysis of findings.
    """
    
    # Regex patterns for secrets detection
    SECRETS_PATTERNS = [
        {
            "name": "AWS Access Key",
            "regex": r"(?i)(AWS_ACCESS_KEY_ID|AKIA[0-9A-Z]{16})",
            "severity": "CRITICAL"
        },
        {
            "name": "AWS Secret Key",
            "regex": r"(?i)(AWS_SECRET_ACCESS_KEY|aws_secret_access_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            "severity": "CRITICAL"
        },
        {
            "name": "GitHub Token",
            "regex": r"(?i)(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})",
            "severity": "CRITICAL"
        },
        {
            "name": "Generic API Key",
            "regex": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
            "severity": "HIGH"
        },
        {
            "name": "Private Key",
            "regex": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
            "severity": "CRITICAL"
        },
        {
            "name": "Generic Password",
            "regex": r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"]([^'\"]{8,})['\"]",
            "severity": "MEDIUM"
        },
        {
            "name": "Database Connection String",
            "regex": r"(?i)(mysql|postgresql|mongodb)://[^\s]+",
            "severity": "HIGH"
        },
        {
            "name": "JWT Token",
            "regex": r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]+",
            "severity": "MEDIUM"
        }
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Security Scanner Agent.
        
        Args:
            config: Security scanner configuration from policies.yaml
        """
        self.config = config
        
        # Initialize tools
        bandit_config = config.get("bandit", {})
        self.bandit = BanditTool(
            confidence_threshold=bandit_config.get("confidence_threshold", "LOW"),
            severity_threshold=bandit_config.get("severity_threshold", "LOW"),
            exclude_tests=bandit_config.get("exclude_tests", [])
        )
        
        safety_config = config.get("safety", {})
        self.safety = SafetyTool(
            ignore_ids=safety_config.get("ignore_ids", []),
            check_unpinned=safety_config.get("check_unpinned", True)
        )
        
        trivy_config = config.get("trivy", {})
        self.trivy = TrivyTool(
            severity_threshold=trivy_config.get("severity_threshold", "CRITICAL,HIGH"),
            scan_types=trivy_config.get("scan_types", ["vuln", "config", "secret"])
        )
        
        # Load custom secrets patterns from config
        secrets_config = config.get("secrets_patterns", {})
        if secrets_config.get("enabled", True) and "patterns" in secrets_config:
            self.secrets_patterns = secrets_config["patterns"]
        else:
            self.secrets_patterns = self.SECRETS_PATTERNS
        
        # Initialize Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Security Scanner initialized with Gemini 1.5 Flash")
        else:
            self.model = None
            logger.warning("No GOOGLE_API_KEY found. Running without AI analysis.")
    
    def scan_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Scan multiple files for security vulnerabilities.
        
        Args:
            file_paths: List of file paths to scan
        
        Returns:
            List of all findings
        """
        all_findings = []
        
        logger.info(f"Starting security scan of {len(file_paths)} file(s)")
        
        for file_path in file_paths:
            try:
                findings = self.scan_file(file_path)
                all_findings.extend(findings)
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        logger.info(f"Security scan complete. Found {len(all_findings)} issue(s)")
        return all_findings
    
    def scan_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan a single file for security issues.
        
        Args:
            file_path: Path to file to scan
        
        Returns:
            List of findings
        """
        findings = []
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return findings
        
        # Run appropriate scans based on file type
        if path.suffix == ".py":
            # Python file - run Bandit and secrets detection
            if self.config.get("bandit", {}).get("enabled", True):
                bandit_findings = self.bandit.scan_file(file_path)
                findings.extend(bandit_findings)
            
            if self.config.get("secrets_patterns", {}).get("enabled", True):
                secrets_findings = self._scan_secrets(file_path)
                findings.extend(secrets_findings)
        
        elif path.name in ["requirements.txt", "Pipfile"]:
            # Requirements file - run Safety
            if self.config.get("safety", {}).get("enabled", True):
                safety_findings = self.safety.scan_requirements(file_path)
                findings.extend(safety_findings)
        
        elif path.suffix in [".dockerfile", ".yaml", ".yml", ".json"]:
            # IaC/Config file - run Trivy if enabled
            if self.config.get("trivy", {}).get("enabled", False):
                trivy_findings = self.trivy.scan_filesystem(file_path)
                findings.extend(trivy_findings)
        
        return findings
    
    def _scan_secrets(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Scan file for hardcoded secrets using regex patterns.
        
        Args:
            file_path: Path to file to scan
        
        Returns:
            List of secret findings
        """
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            for pattern_config in self.secrets_patterns:
                pattern_name = pattern_config["name"]
                pattern = pattern_config["regex"]
                severity = pattern_config["severity"]
                
                # Search for pattern
                matches = list(re.finditer(pattern, content))
                
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    finding = {
                        "tool": "secrets-scanner",
                        "severity": severity,
                        "title": f"Hardcoded secret detected: {pattern_name}",
                        "description": f"Potential {pattern_name} found in code. Hardcoded secrets pose a serious security risk.",
                        "file": file_path,
                        "line_number": line_num,
                        "code_snippet": line_content.strip(),
                        "location": f"{file_path}:L{line_num}",
                        "pattern": pattern_name,
                        "cwe": "CWE-798",
                        "remediation": self._get_secret_remediation(pattern_name)
                    }
                    
                    findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error scanning secrets in {file_path}: {e}")
        
        return findings
    
    def _get_secret_remediation(self, secret_type: str) -> str:
        """
        Get remediation guidance for secret type.
        
        Args:
            secret_type: Type of secret detected
        
        Returns:
            Remediation guidance
        """
        remediations = {
            "AWS Access Key": "Use AWS IAM roles or store credentials in AWS Secrets Manager",
            "AWS Secret Key": "Use AWS IAM roles or store credentials in AWS Secrets Manager",
            "GitHub Token": "Use GitHub secrets or environment variables",
            "Generic API Key": "Store API keys in environment variables or secret management system",
            "Private Key": "Store private keys securely outside of code repository",
            "Generic Password": "Use environment variables or secure secret management",
            "Database Connection String": "Use environment variables for connection strings",
            "JWT Token": "Never hardcode tokens. Generate dynamically and store securely"
        }
        
        return remediations.get(secret_type, "Remove secret from code and use environment variables or secret management system")
    
    def analyze_findings_with_ai(
        self,
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use Gemini to analyze findings and provide insights.
        
        Args:
            findings: List of security findings
        
        Returns:
            Analysis dictionary with insights
        """
        if not self.model or not findings:
            return {"analysis": "AI analysis unavailable"}
        
        try:
            # Prepare summary of findings for AI
            summary = {
                "total": len(findings),
                "by_severity": {},
                "by_tool": {},
                "unique_issues": []
            }
            
            for finding in findings:
                severity = finding.get("severity", "UNKNOWN")
                tool = finding.get("tool", "unknown")
                title = finding.get("title", "")
                
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
                summary["by_tool"][tool] = summary["by_tool"].get(tool, 0) + 1
                
                if title not in summary["unique_issues"]:
                    summary["unique_issues"].append(title)
            
            # Limit to top 10 unique issues for context
            summary["unique_issues"] = summary["unique_issues"][:10]
            
            prompt = f"""
            As a security expert, analyze these security scan findings and provide insights:
            
            Summary:
            - Total findings: {summary['total']}
            - By severity: {summary['by_severity']}
            - By tool: {summary['by_tool']}
            
            Sample issues:
            {chr(10).join(f"- {issue}" for issue in summary['unique_issues'][:5])}
            
            Provide:
            1. Overall security posture assessment (1-2 sentences)
            2. Top 3 priority issues to fix
            3. Quick win recommendations (1-2 sentences)
            
            Keep response concise (max 150 words).
            """
            
            response = self.model.generate_content(prompt)
            
            return {
                "analysis": response.text,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}")
            return {"analysis": "Unable to generate AI analysis"}
    
    def get_summary(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for findings.
        
        Args:
            findings: List of findings
        
        Returns:
            Summary dictionary
        """
        summary = {
            "total": len(findings),
            "by_severity": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            },
            "by_tool": {},
            "by_cwe": {}
        }
        
        for finding in findings:
            severity = finding.get("severity", "LOW")
            tool = finding.get("tool", "unknown")
            cwe = finding.get("cwe", "")
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            summary["by_tool"][tool] = summary["by_tool"].get(tool, 0) + 1
            
            if cwe:
                summary["by_cwe"][cwe] = summary["by_cwe"].get(cwe, 0) + 1
        
        return summary
