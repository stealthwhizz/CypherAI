"""
GitHub Tool
===========

GitHub API client for pull request integration.

This tool handles communication with GitHub's REST API to:
- Post comments on pull requests
- Update PR status checks
- Request changes or approve PRs
- Fetch PR metadata

Documentation: https://docs.github.com/en/rest
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubTool:
    """
    GitHub API client for PR integration.
    
    This class provides methods to interact with GitHub's API
    for posting scan results and updating PR status.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub tool.
        
        Args:
            token: GitHub personal access token (or uses GITHUB_TOKEN env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.api_base = "https://api.github.com"
        
        if not self.token:
            logger.warning("No GitHub token provided. API calls will be limited.")
        
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Get pull request details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
        
        Returns:
            PR data dictionary or None if error
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching PR #{pr_number}: {e}")
            return None
    
    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Get list of files changed in a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
        
        Returns:
            List of file change dictionaries
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching PR files: {e}")
            return []
    
    def post_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        comment: str
    ) -> bool:
        """
        Post a comment on a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            comment: Comment text (Markdown supported)
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        payload = {"body": comment}
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Posted comment on PR #{pr_number}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error posting comment: {e}")
            return False
    
    def update_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str,
        context: str = "Cypher AI Security Scan"
    ) -> bool:
        """
        Update commit status check.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            state: Status state (pending, success, failure, error)
            description: Status description
            context: Status check name
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/statuses/{sha}"
        
        payload = {
            "state": state,
            "description": description[:140],  # Max 140 chars
            "context": context
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Updated status for commit {sha[:7]}: {state}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error updating status: {e}")
            return False
    
    def request_changes(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str
    ) -> bool:
        """
        Submit a review requesting changes.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Review comment body
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "event": "REQUEST_CHANGES",
            "body": body
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Requested changes on PR #{pr_number}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error requesting changes: {e}")
            return False
    
    def approve_pr(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str = "Security scan passed. No issues found."
    ) -> bool:
        """
        Approve a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            body: Review comment body
        
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        payload = {
            "event": "APPROVE",
            "body": body
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Approved PR #{pr_number}")
            return True
        except requests.RequestException as e:
            logger.error(f"Error approving PR: {e}")
            return False
    
    def format_findings_comment(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any],
        decision: str,
        format_type: str = "table"
    ) -> str:
        """
        Format findings into a GitHub comment.
        
        Args:
            findings: Dictionary of findings by category
            summary: Summary statistics
            decision: Merge decision (APPROVE, BLOCK, REVIEW)
            format_type: Comment format (table, list, detailed)
        
        Returns:
            Formatted Markdown comment
        """
        if format_type == "table":
            return self._format_table_comment(findings, summary, decision)
        elif format_type == "detailed":
            return self._format_detailed_comment(findings, summary, decision)
        else:
            return self._format_list_comment(findings, summary, decision)
    
    def _format_table_comment(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any],
        decision: str
    ) -> str:
        """Format findings as a table."""
        icon = {
            "APPROVE": "✅",
            "BLOCK": "🚫",
            "REVIEW": "⚠️"
        }.get(decision, "ℹ️")
        
        comment = f"# {icon} Cypher AI Security Scan Results\n\n"
        
        # Decision
        if decision == "APPROVE":
            comment += "**Status:** ✅ Merge Approved\n\n"
        elif decision == "BLOCK":
            comment += "**Status:** 🚫 Merge Blocked\n\n"
        else:
            comment += "**Status:** ⚠️ Review Required\n\n"
        
        # Summary
        risk_score = summary.get("risk_score", 0)
        severity_breakdown = summary.get("severity_breakdown", {})
        
        comment += f"**Risk Score:** {risk_score}/100\n\n"
        comment += "**Severity Breakdown:**\n"
        comment += f"- 🔴 Critical: {severity_breakdown.get('CRITICAL', 0)}\n"
        comment += f"- 🔴 High: {severity_breakdown.get('HIGH', 0)}\n"
        comment += f"- 🟡 Medium: {severity_breakdown.get('MEDIUM', 0)}\n"
        comment += f"- 🔵 Low: {severity_breakdown.get('LOW', 0)}\n\n"
        
        # Findings table
        total_findings = sum(len(v) for v in findings.values())
        
        if total_findings > 0:
            comment += "## 🔍 Findings\n\n"
            comment += "| Severity | Category | Issue | Location |\n"
            comment += "|----------|----------|-------|----------|\n"
            
            # Combine all findings
            all_findings = []
            for category, category_findings in findings.items():
                for finding in category_findings:
                    all_findings.append({
                        "category": category,
                        **finding
                    })
            
            # Sort by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            all_findings.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 4))
            
            # Show top 20 findings
            for finding in all_findings[:20]:
                severity = finding.get("severity", "UNKNOWN")
                category = finding.get("category", "unknown")
                title = finding.get("title", "Unknown issue")
                location = finding.get("location", "unknown")
                
                # Truncate long titles
                if len(title) > 50:
                    title = title[:47] + "..."
                
                severity_icon = {
                    "CRITICAL": "🔴",
                    "HIGH": "🔴",
                    "MEDIUM": "🟡",
                    "LOW": "🔵"
                }.get(severity, "⚪")
                
                comment += f"| {severity_icon} {severity} | {category} | {title} | `{location}` |\n"
            
            if len(all_findings) > 20:
                comment += f"\n_... and {len(all_findings) - 20} more findings_\n"
        else:
            comment += "## ✅ No Issues Found\n\n"
            comment += "All security checks passed successfully!\n"
        
        # Footer
        comment += "\n---\n"
        comment += f"_Scanned at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_\n"
        comment += "_Powered by [Cypher AI](https://github.com/stealthwhizz/CypherAI)_\n"
        
        return comment
    
    def _format_list_comment(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any],
        decision: str
    ) -> str:
        """Format findings as a list."""
        comment = f"# Cypher AI Security Scan\n\n"
        comment += f"**Decision:** {decision}\n"
        comment += f"**Risk Score:** {summary.get('risk_score', 0)}/100\n\n"
        
        for category, category_findings in findings.items():
            if category_findings:
                comment += f"## {category.title()}\n\n"
                for finding in category_findings[:10]:
                    severity = finding.get("severity", "UNKNOWN")
                    title = finding.get("title", "Unknown")
                    comment += f"- **{severity}**: {title}\n"
                
                if len(category_findings) > 10:
                    comment += f"- _... and {len(category_findings) - 10} more_\n"
                
                comment += "\n"
        
        return comment
    
    def _format_detailed_comment(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any],
        decision: str
    ) -> str:
        """Format findings with full details."""
        comment = self._format_table_comment(findings, summary, decision)
        
        # Add detailed remediation guidance
        comment += "\n## 🔧 Remediation Guidance\n\n"
        
        critical_findings = []
        for category_findings in findings.values():
            critical_findings.extend([
                f for f in category_findings 
                if f.get("severity") == "CRITICAL"
            ])
        
        if critical_findings:
            comment += "### Priority: Critical Issues\n\n"
            for i, finding in enumerate(critical_findings[:5], 1):
                comment += f"{i}. **{finding.get('title', 'Unknown')}**\n"
                remediation = finding.get("remediation", "No remediation guidance available")
                comment += f"   - {remediation}\n\n"
        
        return comment
