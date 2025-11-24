"""
Root Orchestrator Agent
=======================

Coordinates all specialist agents in the multi-agent system.

This agent:
- Receives PR metadata and delegates to specialist agents
- Coordinates parallel execution of security, compliance, and performance scans
- Aggregates findings from all agents
- Makes final merge decision using policy engine
- Generates comprehensive reports

Uses Google Gemini 1.5 Pro for complex reasoning and coordination.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import google.generativeai as genai

from agents.security_scanner import SecurityScannerAgent
from agents.compliance_enforcer import ComplianceEnforcerAgent
from agents.performance_monitor import PerformanceMonitorAgent
from agents.policy_engine import PolicyEngineAgent

logger = logging.getLogger(__name__)


class RootOrchestrator:
    """
    Root Orchestrator Agent for multi-agent coordination.
    
    This is the main entry point that coordinates all specialist agents
    and uses Gemini 1.5 Pro for intelligent orchestration.
    """
    
    def __init__(self, config_path: str = "config/policies.yaml"):
        """
        Initialize Root Orchestrator.
        
        Args:
            config_path: Path to policy configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize Policy Engine first (provides policies for other agents)
        logger.info("Initializing Policy Engine Agent...")
        self.policy_engine = PolicyEngineAgent(config_path)
        
        # Initialize specialist agents
        logger.info("Initializing Security Scanner Agent...")
        self.security_scanner = SecurityScannerAgent(
            self.config.get("security_scanner", {})
        )
        
        logger.info("Initializing Compliance Enforcer Agent...")
        self.compliance_enforcer = ComplianceEnforcerAgent(
            self.config.get("compliance", {})
        )
        
        logger.info("Initializing Performance Monitor Agent...")
        self.performance_monitor = PerformanceMonitorAgent(
            self.config.get("performance_monitor", {})
        )
        
        # Check if parallel execution is enabled
        self.parallel_enabled = self.config.get("performance", {}).get("parallel_agents", True)
        self.max_workers = self.config.get("performance", {}).get("worker_threads", 4)
        
        # Initialize Gemini Pro for orchestration
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Root Orchestrator initialized with Gemini 1.5 Pro")
        else:
            self.model = None
            logger.warning("No GOOGLE_API_KEY found. Running without AI orchestration.")
        
        logger.info("All agents initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def analyze_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pull request and coordinate all agents.
        
        Args:
            pr_data: Pull request metadata including files_changed
        
        Returns:
            Complete analysis results with decision
        """
        start_time = datetime.utcnow()
        
        logger.info("=" * 80)
        logger.info("🔐 Cypher AI - Multi-Agent Security Scan")
        logger.info("=" * 80)
        
        # Extract file paths
        file_paths = pr_data.get("files_changed", [])
        logger.info(f"Analyzing {len(file_paths)} file(s)")
        
        # Delegate to specialist agents
        if self.parallel_enabled:
            findings = self._run_parallel_analysis(file_paths)
        else:
            findings = self._run_sequential_analysis(file_paths)
        
        # Aggregate findings
        logger.info("Aggregating findings from all agents...")
        aggregated = self._aggregate_findings(findings)
        
        # Calculate risk score
        logger.info("Calculating risk score...")
        risk_score = self.policy_engine.calculate_risk_score(aggregated["findings"])
        
        # Generate summary
        summary = self._generate_summary(aggregated["findings"], risk_score)
        
        # Make decision
        logger.info("Making merge decision...")
        decision, reason = self.policy_engine.make_decision(
            aggregated["findings"],
            summary
        )
        
        logger.info(f"Decision: {decision} - {reason}")
        
        # Generate report
        logger.info("Generating report...")
        report_path = self._save_report(aggregated, summary, decision, reason)
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"Scan complete in {duration:.2f} seconds")
        logger.info(f"Status: {decision}")
        logger.info("=" * 80)
        
        return {
            "findings": aggregated["findings"],
            "summary": summary,
            "decision": decision,
            "reason": reason,
            "report_path": report_path,
            "duration": duration,
            "timestamp": start_time.isoformat()
        }
    
    def _run_parallel_analysis(self, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all agents in parallel for faster execution.
        
        Args:
            file_paths: List of files to analyze
        
        Returns:
            Dictionary of findings by agent
        """
        logger.info("Running agents in parallel...")
        
        findings = {
            "security": [],
            "compliance": [],
            "performance": []
        }
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._run_security_scan, file_paths): "security",
                executor.submit(self._run_compliance_check, file_paths): "compliance",
                executor.submit(self._run_performance_analysis, file_paths): "performance"
            }
            
            for future in as_completed(futures):
                agent_type = futures[future]
                try:
                    result = future.result()
                    findings[agent_type] = result
                    logger.info(f"[{agent_type.title()} Agent] Complete: {len(result)} finding(s)")
                except Exception as e:
                    logger.error(f"[{agent_type.title()} Agent] Error: {e}")
        
        return findings
    
    def _run_sequential_analysis(self, file_paths: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run all agents sequentially.
        
        Args:
            file_paths: List of files to analyze
        
        Returns:
            Dictionary of findings by agent
        """
        logger.info("Running agents sequentially...")
        
        findings = {
            "security": self._run_security_scan(file_paths),
            "compliance": self._run_compliance_check(file_paths),
            "performance": self._run_performance_analysis(file_paths)
        }
        
        return findings
    
    def _run_security_scan(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Run security scanner agent."""
        logger.info("[Security Scanner] Starting scan...")
        try:
            findings = self.security_scanner.scan_files(file_paths)
            logger.info(f"[Security Scanner] Found {len(findings)} issue(s)")
            return findings
        except Exception as e:
            logger.error(f"[Security Scanner] Error: {e}")
            return []
    
    def _run_compliance_check(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Run compliance enforcer agent."""
        logger.info("[Compliance Enforcer] Starting validation...")
        try:
            # Get security findings for compliance mapping
            security_findings = self.security_scanner.scan_files(file_paths)
            violations = self.compliance_enforcer.validate_compliance(
                security_findings,
                file_paths
            )
            logger.info(f"[Compliance Enforcer] Found {len(violations)} violation(s)")
            return violations
        except Exception as e:
            logger.error(f"[Compliance Enforcer] Error: {e}")
            return []
    
    def _run_performance_analysis(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Run performance monitor agent."""
        logger.info("[Performance Monitor] Starting analysis...")
        try:
            findings = self.performance_monitor.analyze_files(file_paths)
            logger.info(f"[Performance Monitor] Found {len(findings)} issue(s)")
            return findings
        except Exception as e:
            logger.error(f"[Performance Monitor] Error: {e}")
            return []
    
    def _aggregate_findings(
        self,
        findings: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Aggregate findings from all agents.
        
        Args:
            findings: Dictionary of findings by agent
        
        Returns:
            Aggregated findings dictionary
        """
        return {
            "findings": findings,
            "total_findings": sum(len(v) for v in findings.values())
        }
    
    def _generate_summary(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        risk_score: int
    ) -> Dict[str, Any]:
        """
        Generate summary statistics.
        
        Args:
            findings: All findings
            risk_score: Calculated risk score
        
        Returns:
            Summary dictionary
        """
        # Count by severity
        severity_breakdown = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for category_findings in findings.values():
            for finding in category_findings:
                severity = finding.get("severity", "LOW")
                if severity in severity_breakdown:
                    severity_breakdown[severity] += 1
        
        return {
            "total_findings": sum(len(v) for v in findings.values()),
            "risk_score": risk_score,
            "severity_breakdown": severity_breakdown,
            "by_category": {
                "security": len(findings.get("security", [])),
                "compliance": len(findings.get("compliance", [])),
                "performance": len(findings.get("performance", []))
            }
        }
    
    def _save_report(
        self,
        aggregated: Dict[str, Any],
        summary: Dict[str, Any],
        decision: str,
        reason: str
    ) -> str:
        """
        Save comprehensive report to file.
        
        Args:
            aggregated: Aggregated findings
            summary: Summary statistics
            decision: Merge decision
            reason: Decision reason
        
        Returns:
            Path to saved report
        """
        # Create reports directory if needed
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        report_filename = f"scan_{timestamp}.json"
        report_path = reports_dir / report_filename
        
        # Prepare report data
        report_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision,
            "reason": reason,
            "summary": summary,
            "findings": aggregated["findings"],
            "metadata": {
                "scan_duration": None,
                "agents_used": ["security_scanner", "compliance_enforcer", "performance_monitor"],
                "config_file": self.config_path
            }
        }
        
        # Save JSON report
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
        
        # Also save Markdown report
        md_path = reports_dir / f"scan_{timestamp}.md"
        try:
            md_content = self._generate_markdown_report(
                aggregated, summary, decision, reason
            )
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Markdown report saved to: {md_path}")
        except Exception as e:
            logger.error(f"Error saving markdown report: {e}")
        
        return str(report_path)
    
    def _generate_markdown_report(
        self,
        aggregated: Dict[str, Any],
        summary: Dict[str, Any],
        decision: str,
        reason: str
    ) -> str:
        """Generate Markdown-formatted report."""
        icon = {"APPROVE": "✅", "BLOCK": "🚫", "REVIEW": "⚠️"}.get(decision, "ℹ️")
        
        md = f"# {icon} Cypher AI Security Scan Report\n\n"
        md += f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        
        md += f"## Decision: {decision}\n\n"
        md += f"**Reason:** {reason}\n\n"
        
        md += f"## Summary\n\n"
        md += f"- **Risk Score:** {summary['risk_score']}/100\n"
        md += f"- **Total Findings:** {summary['total_findings']}\n\n"
        
        md += "### By Severity\n\n"
        for severity, count in summary["severity_breakdown"].items():
            md += f"- **{severity}:** {count}\n"
        
        md += "\n### By Category\n\n"
        for category, count in summary["by_category"].items():
            md += f"- **{category.title()}:** {count}\n"
        
        md += "\n## Detailed Findings\n\n"
        
        findings = aggregated["findings"]
        for category, category_findings in findings.items():
            if category_findings:
                md += f"### {category.title()} ({len(category_findings)} findings)\n\n"
                for i, finding in enumerate(category_findings[:20], 1):
                    md += f"#### {i}. {finding.get('title', 'Unknown')}\n\n"
                    md += f"- **Severity:** {finding.get('severity', 'UNKNOWN')}\n"
                    md += f"- **Location:** `{finding.get('location', 'unknown')}`\n"
                    md += f"- **Description:** {finding.get('description', 'No description')[:200]}...\n\n"
        
        return md
