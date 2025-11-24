"""
Policy Engine Agent
===================

Manages security policies, thresholds, and adaptive learning.

This agent:
- Loads and validates policy configurations
- Tracks developer fix patterns for adaptive learning
- Adjusts severity scores based on historical data
- Determines merge pass/fail decisions
- Maintains state across scan sessions

Uses Google Gemini for intelligent policy recommendations.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class PolicyEngineAgent:
    """
    Policy Engine Agent for security policy management and learning.
    
    This agent uses Gemini to provide intelligent policy recommendations
    and learns from developer behavior patterns over time.
    """
    
    def __init__(self, config_path: str = "config/policies.yaml"):
        """
        Initialize Policy Engine Agent.
        
        Args:
            config_path: Path to policy configuration file
        """
        self.config_path = config_path
        self.policies = self._load_policies()
        self.learning_enabled = self.policies.get("learning", {}).get("enabled", True)
        self.state_file = self.policies.get("learning", {}).get(
            "state_file", "config/learning_state.json"
        )
        self.learning_state = self._load_learning_state()
        
        # Initialize Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Policy Engine initialized with Gemini 1.5 Flash")
        else:
            self.model = None
            logger.warning("No GOOGLE_API_KEY found. Running without AI assistance.")
    
    def _load_policies(self) -> Dict[str, Any]:
        """
        Load policy configuration from YAML file.
        
        Returns:
            Policy configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                policies = yaml.safe_load(f)
            logger.info(f"Loaded policies from {self.config_path}")
            return policies
        except FileNotFoundError:
            logger.error(f"Policy file not found: {self.config_path}")
            return self._get_default_policies()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing policy file: {e}")
            return self._get_default_policies()
    
    def _get_default_policies(self) -> Dict[str, Any]:
        """
        Get default policy configuration.
        
        Returns:
            Default policy dictionary
        """
        return {
            "thresholds": {
                "block_on_critical": True,
                "block_on_high": False,
                "max_high_findings": 3,
                "max_medium_findings": 10,
                "risk_score_threshold": 70
            },
            "severity_weights": {
                "CRITICAL": 10,
                "HIGH": 5,
                "MEDIUM": 2,
                "LOW": 1
            },
            "learning": {
                "enabled": True,
                "min_scans_before_adjust": 10,
                "confidence_threshold": 0.7
            }
        }
    
    def _load_learning_state(self) -> Dict[str, Any]:
        """
        Load learning state from file.
        
        Returns:
            Learning state dictionary
        """
        if not self.learning_enabled:
            return {}
        
        try:
            state_path = Path(self.state_file)
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"Loaded learning state from {self.state_file}")
                return state
            else:
                logger.info("No existing learning state found. Starting fresh.")
                return self._init_learning_state()
        except Exception as e:
            logger.error(f"Error loading learning state: {e}")
            return self._init_learning_state()
    
    def _init_learning_state(self) -> Dict[str, Any]:
        """
        Initialize empty learning state.
        
        Returns:
            Empty learning state dictionary
        """
        return {
            "scan_count": 0,
            "finding_patterns": {},
            "developer_actions": {},
            "severity_adjustments": {},
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _save_learning_state(self) -> None:
        """Save learning state to file."""
        if not self.learning_enabled:
            return
        
        try:
            state_path = Path(self.state_file)
            state_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.learning_state["last_updated"] = datetime.utcnow().isoformat()
            
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_state, f, indent=2)
            
            logger.debug(f"Saved learning state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving learning state: {e}")
    
    def get_block_threshold(self) -> Dict[str, Any]:
        """
        Get current block thresholds from policies.
        
        Returns:
            Dictionary with threshold values
        """
        return self.policies.get("thresholds", {})
    
    def calculate_risk_score(
        self,
        findings: Dict[str, List[Dict[str, Any]]]
    ) -> int:
        """
        Calculate overall risk score for findings.
        
        Args:
            findings: Dictionary of findings by category
        
        Returns:
            Risk score (0-100)
        """
        weights = self.policies.get("severity_weights", {})
        total_score = 0
        max_possible = 0
        
        # Flatten all findings
        all_findings = []
        for category_findings in findings.values():
            all_findings.extend(category_findings)
        
        # Calculate weighted score
        for finding in all_findings:
            severity = finding.get("severity", "LOW")
            weight = weights.get(severity, 1)
            total_score += weight
        
        # Assume maximum of 20 critical findings for normalization
        max_possible = weights.get("CRITICAL", 10) * 20
        
        # Normalize to 0-100 scale
        if max_possible > 0:
            risk_score = min(100, int((total_score / max_possible) * 100))
        else:
            risk_score = 0
        
        return risk_score
    
    def make_decision(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Make merge decision based on findings and policies.
        
        Args:
            findings: Dictionary of findings by category
            summary: Summary statistics
        
        Returns:
            Tuple of (decision, reason) where decision is APPROVE, BLOCK, or REVIEW
        """
        thresholds = self.get_block_threshold()
        severity_breakdown = summary.get("severity_breakdown", {})
        risk_score = summary.get("risk_score", 0)
        
        # Check critical threshold
        if thresholds.get("block_on_critical") and severity_breakdown.get("CRITICAL", 0) > 0:
            return (
                "BLOCK",
                f"{severity_breakdown['CRITICAL']} critical vulnerabilit{'y' if severity_breakdown['CRITICAL'] == 1 else 'ies'} found"
            )
        
        # Check high threshold
        high_count = severity_breakdown.get("HIGH", 0)
        if thresholds.get("block_on_high") and high_count > 0:
            return (
                "BLOCK",
                f"{high_count} high severity vulnerabilit{'y' if high_count == 1 else 'ies'} found"
            )
        
        # Check max high findings
        max_high = thresholds.get("max_high_findings", 3)
        if high_count > max_high:
            return (
                "BLOCK",
                f"Too many high severity findings ({high_count} > {max_high})"
            )
        
        # Check max medium findings
        medium_count = severity_breakdown.get("MEDIUM", 0)
        max_medium = thresholds.get("max_medium_findings", 10)
        if medium_count > max_medium:
            return (
                "REVIEW",
                f"Many medium severity findings ({medium_count} > {max_medium})"
            )
        
        # Check risk score
        risk_threshold = thresholds.get("risk_score_threshold", 70)
        if risk_score > risk_threshold:
            return (
                "BLOCK",
                f"Risk score too high ({risk_score} > {risk_threshold})"
            )
        
        # All checks passed
        total_findings = sum(severity_breakdown.values())
        if total_findings == 0:
            return ("APPROVE", "No security issues found")
        else:
            return ("APPROVE", f"All findings below threshold ({total_findings} low-severity issues)")
    
    def adjust_severity(
        self,
        finding: Dict[str, Any],
        developer_history: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adjust finding severity based on learning data.
        
        Args:
            finding: Finding dictionary
            developer_history: Optional developer action history
        
        Returns:
            Adjusted severity level
        """
        if not self.learning_enabled:
            return finding.get("severity", "MEDIUM")
        
        original_severity = finding.get("severity", "MEDIUM")
        finding_type = finding.get("title", "")
        
        # Check if we have enough data
        min_scans = self.policies.get("learning", {}).get("min_scans_before_adjust", 10)
        if self.learning_state.get("scan_count", 0) < min_scans:
            return original_severity
        
        # Check learning state for this finding type
        patterns = self.learning_state.get("finding_patterns", {})
        if finding_type in patterns:
            pattern_data = patterns[finding_type]
            fixed_count = pattern_data.get("fixed", 0)
            ignored_count = pattern_data.get("ignored", 0)
            total = fixed_count + ignored_count
            
            if total > 0:
                fix_rate = fixed_count / total
                confidence_threshold = self.policies.get("learning", {}).get("confidence_threshold", 0.7)
                
                # If developers consistently fix this type, keep or increase severity
                if fix_rate >= confidence_threshold:
                    return original_severity
                
                # If developers consistently ignore, consider decreasing severity
                elif fix_rate < (1 - confidence_threshold):
                    severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                    current_index = severity_levels.index(original_severity) if original_severity in severity_levels else 1
                    
                    # Don't downgrade CRITICAL findings
                    if original_severity != "CRITICAL" and current_index > 0:
                        return severity_levels[current_index - 1]
        
        return original_severity
    
    def record_developer_action(
        self,
        finding: Dict[str, Any],
        action: str
    ) -> None:
        """
        Record developer action on a finding for learning.
        
        Args:
            finding: Finding dictionary
            action: Action taken (fixed, ignored, escalated)
        """
        if not self.learning_enabled:
            return
        
        finding_type = finding.get("title", "unknown")
        
        # Update finding patterns
        patterns = self.learning_state.setdefault("finding_patterns", {})
        if finding_type not in patterns:
            patterns[finding_type] = {"fixed": 0, "ignored": 0, "escalated": 0}
        
        if action in patterns[finding_type]:
            patterns[finding_type][action] += 1
        
        # Update scan count
        self.learning_state["scan_count"] = self.learning_state.get("scan_count", 0) + 1
        
        # Save state
        self._save_learning_state()
        
        logger.debug(f"Recorded {action} action for finding type: {finding_type}")
    
    def get_policy_recommendations(
        self,
        findings: Dict[str, List[Dict[str, Any]]],
        summary: Dict[str, Any]
    ) -> str:
        """
        Get AI-powered policy recommendations.
        
        Args:
            findings: Dictionary of findings
            summary: Summary statistics
        
        Returns:
            Recommendations text
        """
        if not self.model:
            return "AI recommendations unavailable (no API key configured)"
        
        try:
            # Prepare context for Gemini
            prompt = f"""
            As a security policy expert, analyze these security scan results and provide recommendations
            for adjusting security policies.
            
            Summary:
            - Total findings: {summary.get('total_findings', 0)}
            - Risk score: {summary.get('risk_score', 0)}/100
            - Critical: {summary.get('severity_breakdown', {}).get('CRITICAL', 0)}
            - High: {summary.get('severity_breakdown', {}).get('HIGH', 0)}
            - Medium: {summary.get('severity_breakdown', {}).get('MEDIUM', 0)}
            - Low: {summary.get('severity_breakdown', {}).get('LOW', 0)}
            
            Current thresholds:
            {json.dumps(self.policies.get('thresholds', {}), indent=2)}
            
            Provide:
            1. Assessment of current policy effectiveness
            2. Specific threshold adjustments (if needed)
            3. Rationale for changes
            
            Keep response concise (max 200 words).
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting policy recommendations: {e}")
            return "Unable to generate recommendations at this time"
    
    def validate_policies(self) -> List[str]:
        """
        Validate policy configuration for issues.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check required sections
        required_sections = ["thresholds", "severity_weights"]
        for section in required_sections:
            if section not in self.policies:
                issues.append(f"Missing required section: {section}")
        
        # Check threshold values
        thresholds = self.policies.get("thresholds", {})
        if thresholds.get("max_high_findings", 0) < 1:
            issues.append("max_high_findings should be at least 1")
        
        if thresholds.get("risk_score_threshold", 0) > 100:
            issues.append("risk_score_threshold cannot exceed 100")
        
        # Check severity weights
        weights = self.policies.get("severity_weights", {})
        required_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for severity in required_severities:
            if severity not in weights:
                issues.append(f"Missing severity weight: {severity}")
        
        return issues
