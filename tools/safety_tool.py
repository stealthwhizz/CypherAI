"""
Safety Tool Wrapper
===================

Wrapper for Safety dependency vulnerability scanner.

Safety checks Python dependencies for known security vulnerabilities
by comparing them against a database of insecure packages.

Documentation: https://pyup.io/safety/
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class SafetyTool:
    """
    Wrapper for Safety dependency scanner.
    
    This class provides methods to scan Python requirements files
    for known vulnerabilities and parse results into standardized format.
    """
    
    def __init__(
        self,
        ignore_ids: Optional[List[str]] = None,
        check_unpinned: bool = True
    ):
        """
        Initialize Safety tool wrapper.
        
        Args:
            ignore_ids: List of vulnerability IDs to ignore
            check_unpinned: Whether to warn about unpinned dependencies
        """
        self.ignore_ids = ignore_ids or []
        self.check_unpinned = check_unpinned
        
        # Check if Safety is installed
        if not self._check_installed():
            logger.warning("Safety is not installed. Install with: pip install safety")
    
    def _check_installed(self) -> bool:
        """
        Check if Safety is installed.
        
        Returns:
            True if Safety is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["safety", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_requirements(self, requirements_file: str) -> List[Dict[str, Any]]:
        """
        Scan requirements file for vulnerable dependencies.
        
        Args:
            requirements_file: Path to requirements.txt file
        
        Returns:
            List of vulnerability findings
        
        Raises:
            FileNotFoundError: If requirements file doesn't exist
        """
        path = Path(requirements_file)
        
        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")
        
        if not self._check_installed():
            logger.error("Safety is not installed")
            return []
        
        try:
            # Build Safety command
            cmd = [
                "safety",
                "check",
                "--file", str(path),
                "--json",
                "--output", "json"
            ]
            
            # Add ignore IDs if specified
            if self.ignore_ids:
                for vuln_id in self.ignore_ids:
                    cmd.extend(["--ignore", vuln_id])
            
            # Run Safety
            logger.info(f"Running Safety on {requirements_file}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Safety returns non-zero if vulnerabilities found, which is expected
            # Parse output even if return code is not 0
            findings = self._parse_results(result.stdout, requirements_file)
            
            # Check for unpinned dependencies if enabled
            if self.check_unpinned:
                unpinned_findings = self._check_unpinned_deps(requirements_file)
                findings.extend(unpinned_findings)
            
            logger.info(f"Safety found {len(findings)} issue(s) in {requirements_file}")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error(f"Safety scan timed out for {requirements_file}")
            return []
        except Exception as e:
            logger.error(f"Error running Safety on {requirements_file}: {e}")
            return []
    
    def scan_installed_packages(self) -> List[Dict[str, Any]]:
        """
        Scan currently installed packages for vulnerabilities.
        
        Returns:
            List of vulnerability findings
        """
        if not self._check_installed():
            logger.error("Safety is not installed")
            return []
        
        try:
            # Run Safety on installed packages
            cmd = ["safety", "check", "--json"]
            
            # Add ignore IDs if specified
            if self.ignore_ids:
                for vuln_id in self.ignore_ids:
                    cmd.extend(["--ignore", vuln_id])
            
            logger.info("Running Safety on installed packages")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            findings = self._parse_results(result.stdout, "installed packages")
            
            logger.info(f"Safety found {len(findings)} issue(s) in installed packages")
            return findings
            
        except subprocess.TimeoutExpired:
            logger.error("Safety scan timed out")
            return []
        except Exception as e:
            logger.error(f"Error running Safety: {e}")
            return []
    
    def _parse_results(self, output: str, source: str) -> List[Dict[str, Any]]:
        """
        Parse Safety JSON output into standardized format.
        
        Args:
            output: Safety JSON output string
            source: Source file or "installed packages"
        
        Returns:
            List of standardized findings
        """
        try:
            # Safety outputs JSON array
            data = json.loads(output) if output.strip() else []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Safety output: {e}")
            # Try to extract useful info from text output
            return self._parse_text_output(output, source)
        
        findings = []
        
        for vuln in data:
            # Extract vulnerability details
            package_name = vuln.get("package", "unknown")
            installed_version = vuln.get("installed_version", "unknown")
            affected_versions = vuln.get("affected_versions", "")
            vulnerability_id = vuln.get("vulnerability_id", "")
            cve = vuln.get("CVE", "")
            description = vuln.get("advisory", "")
            
            # Determine severity from description or CVE score
            severity = self._determine_severity(vuln)
            
            finding = {
                "tool": "safety",
                "severity": severity,
                "title": f"Vulnerable dependency: {package_name}=={installed_version}",
                "description": self._build_description(vuln),
                "package": package_name,
                "installed_version": installed_version,
                "affected_versions": affected_versions,
                "vulnerability_id": vulnerability_id,
                "cve": cve,
                "file": source,
                "location": f"{source}:{package_name}",
                "remediation": self._build_remediation(vuln)
            }
            
            findings.append(finding)
        
        return findings
    
    def _parse_text_output(self, output: str, source: str) -> List[Dict[str, Any]]:
        """
        Parse Safety text output as fallback.
        
        Args:
            output: Safety text output
            source: Source file
        
        Returns:
            List of findings
        """
        findings = []
        
        # Look for vulnerability patterns in text
        lines = output.split('\n')
        current_vuln = {}
        
        for line in lines:
            line = line.strip()
            
            # Try to extract package and version
            if '->' in line or '==' in line:
                match = re.search(r'(\w+)\s*==\s*([\d.]+)', line)
                if match:
                    package, version = match.groups()
                    current_vuln = {
                        "tool": "safety",
                        "severity": "MEDIUM",
                        "title": f"Vulnerable dependency: {package}=={version}",
                        "package": package,
                        "installed_version": version,
                        "file": source,
                        "location": f"{source}:{package}"
                    }
                    findings.append(current_vuln)
        
        return findings
    
    def _determine_severity(self, vuln: Dict[str, Any]) -> str:
        """
        Determine severity level from vulnerability data.
        
        Args:
            vuln: Vulnerability dictionary from Safety
        
        Returns:
            Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        """
        # Check for severity hints in advisory text
        advisory = vuln.get("advisory", "").lower()
        cve = vuln.get("CVE", "")
        
        # Critical indicators
        critical_keywords = [
            "remote code execution", "rce", "arbitrary code",
            "critical", "sql injection", "command injection"
        ]
        
        # High severity indicators
        high_keywords = [
            "denial of service", "dos", "security bypass",
            "authentication bypass", "privilege escalation"
        ]
        
        # Check for critical indicators
        for keyword in critical_keywords:
            if keyword in advisory:
                return "CRITICAL"
        
        # Check for high severity indicators
        for keyword in high_keywords:
            if keyword in advisory:
                return "HIGH"
        
        # If CVE is present, default to HIGH
        if cve and cve != "CVE-NOTASSIGNED":
            return "HIGH"
        
        # Default to MEDIUM
        return "MEDIUM"
    
    def _build_description(self, vuln: Dict[str, Any]) -> str:
        """
        Build detailed description from vulnerability data.
        
        Args:
            vuln: Vulnerability dictionary
        
        Returns:
            Detailed description string
        """
        package = vuln.get("package", "unknown")
        version = vuln.get("installed_version", "unknown")
        advisory = vuln.get("advisory", "No description available")
        vuln_id = vuln.get("vulnerability_id", "")
        cve = vuln.get("CVE", "")
        
        description = f"Package: {package} {version}\n\n"
        description += f"{advisory}\n"
        
        if vuln_id:
            description += f"\nVulnerability ID: {vuln_id}"
        
        if cve and cve != "CVE-NOTASSIGNED":
            description += f"\nCVE: {cve}"
        
        affected = vuln.get("affected_versions", "")
        if affected:
            description += f"\n\nAffected versions: {affected}"
        
        return description
    
    def _build_remediation(self, vuln: Dict[str, Any]) -> str:
        """
        Build remediation guidance.
        
        Args:
            vuln: Vulnerability dictionary
        
        Returns:
            Remediation guidance string
        """
        package = vuln.get("package", "unknown")
        
        # Safety doesn't always provide safe versions in JSON output
        # Provide general guidance
        remediation = f"Update {package} to the latest secure version.\n\n"
        remediation += "Run: pip install --upgrade {}\n".format(package)
        remediation += "Or pin to a specific secure version in requirements.txt"
        
        return remediation
    
    def _check_unpinned_deps(self, requirements_file: str) -> List[Dict[str, Any]]:
        """
        Check for unpinned dependencies in requirements file.
        
        Args:
            requirements_file: Path to requirements file
        
        Returns:
            List of findings for unpinned dependencies
        """
        findings = []
        
        try:
            with open(requirements_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Check if version is pinned (contains ==)
                if '==' not in line and line and not line.startswith('-'):
                    # Extract package name
                    package = line.split('[')[0].split('>')[0].split('<')[0].split('!')[0].strip()
                    
                    if package:
                        finding = {
                            "tool": "safety",
                            "severity": "LOW",
                            "title": f"Unpinned dependency: {package}",
                            "description": (
                                f"Package '{package}' is not pinned to a specific version. "
                                "This can lead to unexpected behavior when dependencies are updated.\n\n"
                                "Recommendation: Pin to a specific version using '==' operator.\n"
                                f"Example: {package}==1.2.3"
                            ),
                            "package": package,
                            "file": requirements_file,
                            "line_number": line_num,
                            "location": f"{requirements_file}:L{line_num}",
                            "remediation": f"Pin {package} to a specific version: {package}==X.Y.Z"
                        }
                        
                        findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error checking unpinned dependencies: {e}")
        
        return findings
    
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
            "vulnerable_packages": set(),
            "cves": []
        }
        
        for finding in findings:
            severity = finding.get("severity", "MEDIUM")
            package = finding.get("package", "")
            cve = finding.get("cve", "")
            
            if severity in summary["by_severity"]:
                summary["by_severity"][severity] += 1
            
            if package:
                summary["vulnerable_packages"].add(package)
            
            if cve and cve != "CVE-NOTASSIGNED":
                summary["cves"].append(cve)
        
        summary["vulnerable_packages"] = list(summary["vulnerable_packages"])
        
        return summary
