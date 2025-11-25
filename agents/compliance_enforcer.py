"""
Compliance Enforcer Agent
==========================

Validates compliance with security frameworks and regulations.

This agent:
- Maps security findings to compliance requirements
- Validates PCI DSS, HIPAA, SOC 2, GDPR compliance
- Generates audit-ready compliance reports
- Checks for framework-specific violations

Uses Google Gemini for intelligent compliance mapping.
"""

import os
from typing import Dict, Any, List, Optional
import logging

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

logger = logging.getLogger(__name__)


class ComplianceEnforcerAgent:
    """
    Compliance Enforcer Agent for regulatory validation.
    
    This agent ensures code changes comply with security frameworks
    and uses Gemini for intelligent compliance analysis.
    """
    
    # Compliance framework mappings
    PCI_DSS_MAPPINGS = {
        "SQL Injection": ["6.5.1"],
        "Command Injection": ["6.5.1"],
        "XSS": ["6.5.7"],
        "Weak Cryptography": ["6.5.3", "3.4"],
        "Hardcoded Secret": ["3.4", "8.2.3"],
        "Insecure Deserialization": ["6.5.8"],
        "Authentication": ["8.2.3", "8.2.4"],
        "Access Control": ["6.5.8", "7.1"]
    }
    
    HIPAA_PATTERNS = {
        "PHI": [
            r"(?i)(ssn|social.security)",
            r"(?i)(medical.record|mrn)",
            r"(?i)(patient.id|health.record)",
            r"\d{3}-\d{2}-\d{4}"  # SSN pattern
        ],
        "Encryption": [
            r"(?i)(encrypt|aes|rsa)",
            r"(?i)(ssl|tls|https)"
        ]
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Compliance Enforcer Agent.
        
        Args:
            config: Compliance configuration from policies.yaml
        """
        self.config = config
        self.enabled_frameworks = self._get_enabled_frameworks()
        
        # Initialize ADK Agent with Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            
            # Configure retry options
            retry_config = types.HttpRetryOptions(
                attempts=5,
                exp_base=7,
                initial_delay=1,
                http_status_codes=[429, 500, 503, 504]
            )
            
            # Create ADK Agent for compliance analysis
            self.agent = LlmAgent(
                name="compliance_enforcer",
                model=Gemini(
                    model="gemini-1.5-flash",
                    retry_options=retry_config
                ),
                description="Compliance enforcer that validates security frameworks and regulations",
                instruction="""You are a compliance expert specializing in security frameworks.
                Analyze security findings and map them to compliance requirements for PCI DSS, HIPAA, SOC 2, and GDPR.
                Provide clear compliance violation reports."""
            )
            
            # Create runner
            self.runner = InMemoryRunner(agent=self.agent)
            
            logger.info("Compliance Enforcer initialized with ADK Gemini 1.5 Flash")
        else:
            self.agent = None
            self.runner = None
            logger.warning("No GOOGLE_API_KEY found. Running without AI assistance.")
    
    def _get_enabled_frameworks(self) -> List[str]:
        """
        Get list of enabled compliance frameworks.
        
        Returns:
            List of enabled framework names
        """
        enabled = []
        
        if self.config.get("pci_dss", {}).get("enabled", False):
            enabled.append("PCI DSS")
        
        if self.config.get("hipaa", {}).get("enabled", False):
            enabled.append("HIPAA")
        
        if self.config.get("soc2", {}).get("enabled", False):
            enabled.append("SOC 2")
        
        if self.config.get("gdpr", {}).get("enabled", False):
            enabled.append("GDPR")
        
        return enabled
    
    def validate_compliance(
        self,
        security_findings: List[Dict[str, Any]],
        file_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Validate compliance across all enabled frameworks.
        
        Args:
            security_findings: List of security findings from scanner
            file_paths: List of files to check
        
        Returns:
            List of compliance violations
        """
        violations = []
        
        logger.info(f"Checking compliance for frameworks: {', '.join(self.enabled_frameworks)}")
        
        if "PCI DSS" in self.enabled_frameworks:
            pci_violations = self._check_pci_dss(security_findings)
            violations.extend(pci_violations)
        
        if "HIPAA" in self.enabled_frameworks:
            hipaa_violations = self._check_hipaa(security_findings, file_paths)
            violations.extend(hipaa_violations)
        
        if "SOC 2" in self.enabled_frameworks:
            soc2_violations = self._check_soc2(security_findings)
            violations.extend(soc2_violations)
        
        if "GDPR" in self.enabled_frameworks:
            gdpr_violations = self._check_gdpr(security_findings, file_paths)
            violations.extend(gdpr_violations)
        
        logger.info(f"Found {len(violations)} compliance violation(s)")
        return violations
    
    def _check_pci_dss(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check PCI DSS compliance.
        
        Args:
            findings: Security findings
        
        Returns:
            List of PCI DSS violations
        """
        violations = []
        strict_mode = self.config.get("pci_dss", {}).get("strict_mode", False)
        required_requirements = self.config.get("pci_dss", {}).get("requirements", [])
        
        for finding in findings:
            title = finding.get("title", "")
            description = finding.get("description", "")
            
            # Map finding to PCI DSS requirements
            mapped_requirements = []
            
            for pattern, requirements in self.PCI_DSS_MAPPINGS.items():
                if pattern.lower() in title.lower() or pattern.lower() in description.lower():
                    mapped_requirements.extend(requirements)
            
            if mapped_requirements:
                # Filter to only required requirements if specified
                if required_requirements:
                    mapped_requirements = [
                        req for req in mapped_requirements 
                        if req in required_requirements
                    ]
                
                if mapped_requirements:
                    severity = "HIGH" if strict_mode else finding.get("severity", "MEDIUM")
                    
                    violation = {
                        "tool": "compliance-enforcer",
                        "framework": "PCI DSS",
                        "severity": severity,
                        "title": f"PCI DSS {', '.join(mapped_requirements)}: {title}",
                        "description": f"This finding violates PCI DSS requirement(s): {', '.join(mapped_requirements)}\n\n{description}",
                        "requirements": mapped_requirements,
                        "file": finding.get("file", ""),
                        "location": finding.get("location", ""),
                        "original_finding": finding,
                        "remediation": self._get_pci_remediation(mapped_requirements)
                    }
                    
                    violations.append(violation)
        
        return violations
    
    def _check_hipaa(
        self,
        findings: List[Dict[str, Any]],
        file_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check HIPAA compliance.
        
        Args:
            findings: Security findings
            file_paths: Files to check
        
        Returns:
            List of HIPAA violations
        """
        violations = []
        check_phi = self.config.get("hipaa", {}).get("check_phi_patterns", True)
        
        if not check_phi:
            return violations
        
        import re
        
        # Check for PHI patterns in code
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, start=1):
                    for pattern in self.HIPAA_PATTERNS["PHI"]:
                        if re.search(pattern, line):
                            violation = {
                                "tool": "compliance-enforcer",
                                "framework": "HIPAA",
                                "severity": "CRITICAL",
                                "title": "Potential PHI exposure",
                                "description": "Code may contain or process Protected Health Information (PHI) without proper safeguards",
                                "file": file_path,
                                "line_number": line_num,
                                "location": f"{file_path}:L{line_num}",
                                "code_snippet": line.strip(),
                                "remediation": "Ensure PHI is encrypted at rest and in transit. Use appropriate access controls."
                            }
                            violations.append(violation)
                            break
            
            except Exception as e:
                logger.error(f"Error checking HIPAA compliance in {file_path}: {e}")
        
        # Map existing findings to HIPAA violations
        for finding in findings:
            if finding.get("severity") in ["CRITICAL", "HIGH"]:
                if any(keyword in finding.get("title", "").lower() 
                       for keyword in ["encryption", "authentication", "access"]):
                    violation = {
                        "tool": "compliance-enforcer",
                        "framework": "HIPAA",
                        "severity": "HIGH",
                        "title": f"HIPAA Security Rule: {finding.get('title', '')}",
                        "description": f"This finding may violate HIPAA Security Rule requirements.\n\n{finding.get('description', '')}",
                        "file": finding.get("file", ""),
                        "location": finding.get("location", ""),
                        "original_finding": finding,
                        "remediation": "Review HIPAA Security Rule requirements and implement appropriate safeguards"
                    }
                    violations.append(violation)
        
        return violations
    
    def _check_soc2(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check SOC 2 compliance.
        
        Args:
            findings: Security findings
        
        Returns:
            List of SOC 2 violations
        """
        violations = []
        categories = self.config.get("soc2", {}).get("categories", ["security"])
        
        # SOC 2 focuses on security, availability, confidentiality
        soc2_keywords = {
            "security": ["authentication", "authorization", "encryption", "access control"],
            "availability": ["performance", "uptime", "resilience"],
            "confidentiality": ["secret", "credential", "sensitive data"]
        }
        
        for finding in findings:
            if finding.get("severity") in ["CRITICAL", "HIGH"]:
                title_lower = finding.get("title", "").lower()
                
                for category in categories:
                    keywords = soc2_keywords.get(category, [])
                    if any(keyword in title_lower for keyword in keywords):
                        violation = {
                            "tool": "compliance-enforcer",
                            "framework": "SOC 2",
                            "severity": finding.get("severity", "HIGH"),
                            "title": f"SOC 2 {category.title()}: {finding.get('title', '')}",
                            "description": f"This finding may impact SOC 2 {category} trust service criteria.\n\n{finding.get('description', '')}",
                            "category": category,
                            "file": finding.get("file", ""),
                            "location": finding.get("location", ""),
                            "original_finding": finding,
                            "remediation": f"Address this issue to maintain SOC 2 {category} compliance"
                        }
                        violations.append(violation)
                        break
        
        return violations
    
    def _check_gdpr(
        self,
        findings: List[Dict[str, Any]],
        file_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Check GDPR compliance.
        
        Args:
            findings: Security findings
            file_paths: Files to check
        
        Returns:
            List of GDPR violations
        """
        violations = []
        check_pii = self.config.get("gdpr", {}).get("check_pii_patterns", True)
        
        if not check_pii:
            return violations
        
        # GDPR PII patterns
        pii_patterns = [
            r"(?i)(email|e-mail)\s*[=:]\s*['\"]?[\w\.-]+@[\w\.-]+",
            r"(?i)(phone|tel|mobile)\s*[=:]\s*['\"]?[\d\-\(\)\+\s]+",
            r"(?i)(address|location|zip|postal)",
        ]
        
        import re
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern in pii_patterns:
                    matches = list(re.finditer(pattern, content))
                    if matches:
                        line_num = content[:matches[0].start()].count('\n') + 1
                        
                        violation = {
                            "tool": "compliance-enforcer",
                            "framework": "GDPR",
                            "severity": "HIGH",
                            "title": "Potential PII processing detected",
                            "description": "Code may process Personal Identifiable Information (PII). Ensure GDPR compliance including consent, data minimization, and right to deletion.",
                            "file": file_path,
                            "line_number": line_num,
                            "location": f"{file_path}:L{line_num}",
                            "remediation": "Implement GDPR-compliant data handling: obtain consent, minimize data collection, enable data deletion"
                        }
                        violations.append(violation)
                        break
            
            except Exception as e:
                logger.error(f"Error checking GDPR compliance in {file_path}: {e}")
        
        return violations
    
    def _get_pci_remediation(self, requirements: List[str]) -> str:
        """
        Get remediation guidance for PCI DSS requirements.
        
        Args:
            requirements: List of PCI DSS requirement numbers
        
        Returns:
            Remediation guidance
        """
        remediation_map = {
            "6.5.1": "Implement input validation and use parameterized queries to prevent injection attacks",
            "6.5.3": "Use strong cryptography (AES-256, RSA-2048+) to protect sensitive data",
            "6.5.7": "Implement output encoding to prevent XSS attacks",
            "6.5.8": "Implement proper authentication and access control mechanisms",
            "3.4": "Encrypt sensitive authentication data and card holder data",
            "8.2.3": "Implement multi-factor authentication for all user access",
            "7.1": "Limit access to system components based on need-to-know"
        }
        
        remediations = [remediation_map.get(req, f"Review PCI DSS requirement {req}") for req in requirements]
        return " | ".join(remediations)
    
    def generate_compliance_report(
        self,
        violations: List[Dict[str, Any]]
    ) -> str:
        """
        Generate audit-ready compliance report.
        
        Args:
            violations: List of compliance violations
        
        Returns:
            Markdown-formatted compliance report
        """
        report = "# Compliance Report\n\n"
        report += f"**Generated:** {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        
        # Summary by framework
        frameworks = {}
        for violation in violations:
            framework = violation.get("framework", "Unknown")
            frameworks[framework] = frameworks.get(framework, 0) + 1
        
        report += "## Summary\n\n"
        for framework, count in frameworks.items():
            status = "❌ FAIL" if count > 0 else "✅ PASS"
            report += f"- **{framework}**: {status} ({count} violation(s))\n"
        
        report += "\n## Violations by Framework\n\n"
        
        # Group violations by framework
        for framework in frameworks.keys():
            framework_violations = [v for v in violations if v.get("framework") == framework]
            
            report += f"### {framework}\n\n"
            report += f"Total violations: {len(framework_violations)}\n\n"
            
            for i, violation in enumerate(framework_violations, 1):
                report += f"#### {i}. {violation.get('title', 'Unknown')}\n\n"
                report += f"**Severity:** {violation.get('severity', 'UNKNOWN')}\n\n"
                report += f"**Location:** `{violation.get('location', 'unknown')}`\n\n"
                report += f"**Description:**\n{violation.get('description', 'No description')}\n\n"
                report += f"**Remediation:**\n{violation.get('remediation', 'No remediation guidance')}\n\n"
                report += "---\n\n"
        
        return report
    
    def get_summary(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for violations.
        
        Args:
            violations: List of compliance violations
        
        Returns:
            Summary dictionary
        """
        summary = {
            "total": len(violations),
            "by_framework": {},
            "by_severity": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            }
        }
        
        for violation in violations:
            framework = violation.get("framework", "Unknown")
            severity = violation.get("severity", "MEDIUM")
            
            summary["by_framework"][framework] = summary["by_framework"].get(framework, 0) + 1
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
        
        return summary
