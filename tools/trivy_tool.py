"""
Trivy Tool Wrapper
==================

Wrapper for Trivy container and IaC security scanner.

Trivy is a comprehensive security scanner for containers, Kubernetes,
infrastructure as code, and more.

Documentation: https://trivy.dev/
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TrivyTool:
    """
    Wrapper for Trivy security scanner.
    
    This class provides methods to scan containers, filesystems,
    and IaC configurations for vulnerabilities.
    
    Note: Trivy must be installed separately from the system package manager.
    """
    
    SEVERITY_MAP = {
        "CRITICAL": "CRITICAL",
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW",
        "UNKNOWN": "LOW"
    }
    
    def __init__(
        self,
        severity_threshold: str = "CRITICAL,HIGH",
        scan_types: Optional[List[str]] = None
    ):
        """
        Initialize Trivy tool wrapper.
        
        Args:
            severity_threshold: Comma-separated severity levels to report
            scan_types: Types of scans to perform (vuln, config, secret)
        """
        self.severity_threshold = severity_threshold
        self.scan_types = scan_types or ["vuln", "config", "secret"]
        
        # Check if Trivy is installed
        if not self._check_installed():
            logger.warning(
                "Trivy is not installed. "
                "Install from: https://aquasecurity.github.io/trivy/"
            )
    
    def _check_installed(self) -> bool:
        """
        Check if Trivy is installed.
        
        Returns:
            True if Trivy is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["trivy", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_filesystem(self, path: str) -> List[Dict[str, Any]]:
        """
        Scan filesystem for vulnerabilities and misconfigurations.
        
        Args:
            path: Path to scan (file or directory)
        
        Returns:
            List of findings
        
        Raises:
            FileNotFoundError: If path doesn't exist
        """
        target_path = Path(path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if not self._check_installed():
            logger.warning("Trivy not installed, skipping scan")
            return []
        
        try:
            # Create temporary file for JSON output
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                output_file = tmp.name
            
            # Build Trivy command
            cmd = [
                "trivy",
                "filesystem",
                "--format", "json",
                "--output", output_file,
                "--severity", self.severity_threshold,
            ]
            
            # Add scan types
            for scan_type in self.scan_types:
                cmd.extend(["--scanners", scan_type])
            
            cmd.append(str(target_path))
            
            # Run Trivy
            logger.info(f"Running Trivy on {path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse results
            findings = self._parse_results(output_file, path)
            
            # Clean up
            Path(output_file).unlink(missing_ok=True)
            
            logger.info(f"Trivy found {len(findings)} issue(s) in {path}")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error(f"Trivy scan timed out for {path}")
            return []
        except Exception as e:
            logger.error(f"Error running Trivy on {path}: {e}")
            return []
    
    def scan_container_image(self, image: str) -> List[Dict[str, Any]]:
        """
        Scan container image for vulnerabilities.
        
        Args:
            image: Container image name (e.g., "nginx:latest")
        
        Returns:
            List of findings
        """
        if not self._check_installed():
            logger.warning("Trivy not installed, skipping scan")
            return []
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                output_file = tmp.name
            
            cmd = [
                "trivy",
                "image",
                "--format", "json",
                "--output", output_file,
                "--severity", self.severity_threshold,
                image
            ]
            
            logger.info(f"Running Trivy on container image {image}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # Container scans can take longer
            )
            
            findings = self._parse_results(output_file, f"image:{image}")
            
            Path(output_file).unlink(missing_ok=True)
            
            logger.info(f"Trivy found {len(findings)} issue(s) in {image}")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error(f"Trivy scan timed out for {image}")
            return []
        except Exception as e:
            logger.error(f"Error running Trivy on {image}: {e}")
            return []
    
    def _parse_results(self, output_file: str, source: str) -> List[Dict[str, Any]]:
        """
        Parse Trivy JSON output into standardized format.
        
        Args:
            output_file: Path to Trivy JSON output
            source: Source that was scanned
        
        Returns:
            List of standardized findings
        """
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error reading Trivy output: {e}")
            return []
        
        findings = []
        
        # Trivy output structure: Results array with Vulnerabilities and Misconfigurations
        results = data.get("Results", [])
        
        for result in results:
            target = result.get("Target", source)
            
            # Parse vulnerabilities
            vulnerabilities = result.get("Vulnerabilities", [])
            for vuln in vulnerabilities:
                finding = self._parse_vulnerability(vuln, target)
                findings.append(finding)
            
            # Parse misconfigurations
            misconfigs = result.get("Misconfigurations", [])
            for misconfig in misconfigs:
                finding = self._parse_misconfiguration(misconfig, target)
                findings.append(finding)
            
            # Parse secrets
            secrets = result.get("Secrets", [])
            for secret in secrets:
                finding = self._parse_secret(secret, target)
                findings.append(finding)
        
        return findings
    
    def _parse_vulnerability(self, vuln: Dict[str, Any], target: str) -> Dict[str, Any]:
        """Parse vulnerability finding."""
        return {
            "tool": "trivy",
            "type": "vulnerability",
            "severity": self.SEVERITY_MAP.get(vuln.get("Severity", "UNKNOWN"), "LOW"),
            "title": f"Vulnerability in {vuln.get('PkgName', 'unknown')}: {vuln.get('VulnerabilityID', '')}",
            "description": vuln.get("Description", "No description available"),
            "vulnerability_id": vuln.get("VulnerabilityID", ""),
            "package": vuln.get("PkgName", ""),
            "installed_version": vuln.get("InstalledVersion", ""),
            "fixed_version": vuln.get("FixedVersion", ""),
            "cve": vuln.get("VulnerabilityID", "") if "CVE" in vuln.get("VulnerabilityID", "") else "",
            "references": vuln.get("References", []),
            "file": target,
            "location": target,
            "remediation": self._build_vuln_remediation(vuln)
        }
    
    def _parse_misconfiguration(self, misconfig: Dict[str, Any], target: str) -> Dict[str, Any]:
        """Parse misconfiguration finding."""
        return {
            "tool": "trivy",
            "type": "misconfiguration",
            "severity": self.SEVERITY_MAP.get(misconfig.get("Severity", "UNKNOWN"), "LOW"),
            "title": misconfig.get("Title", "Configuration issue"),
            "description": misconfig.get("Description", ""),
            "check_id": misconfig.get("ID", ""),
            "file": target,
            "location": target,
            "remediation": misconfig.get("Resolution", "Review and fix the configuration issue")
        }
    
    def _parse_secret(self, secret: Dict[str, Any], target: str) -> Dict[str, Any]:
        """Parse secret finding."""
        return {
            "tool": "trivy",
            "type": "secret",
            "severity": "CRITICAL",
            "title": f"Secret detected: {secret.get('Title', 'Unknown')}",
            "description": f"Potential secret found: {secret.get('Match', '')}",
            "rule_id": secret.get("RuleID", ""),
            "category": secret.get("Category", ""),
            "file": target,
            "location": target,
            "remediation": "Remove the secret and use environment variables or secret management systems"
        }
    
    def _build_vuln_remediation(self, vuln: Dict[str, Any]) -> str:
        """Build remediation guidance for vulnerability."""
        package = vuln.get("PkgName", "unknown")
        fixed_version = vuln.get("FixedVersion", "")
        
        if fixed_version:
            return f"Update {package} to version {fixed_version} or later"
        else:
            return f"No fix available yet for {package}. Consider using an alternative package or implementing additional security controls"
    
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
            "by_type": {
                "vulnerability": 0,
                "misconfiguration": 0,
                "secret": 0
            },
            "cves": []
        }
        
        for finding in findings:
            severity = finding.get("severity", "LOW")
            finding_type = finding.get("type", "unknown")
            cve = finding.get("cve", "")
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            if finding_type in summary["by_type"]:
                summary["by_type"][finding_type] += 1
            
            if cve:
                summary["cves"].append(cve)
        
        return summary
