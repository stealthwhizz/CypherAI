"""
Security Tools Integration
===========================

This package contains wrapper classes for security scanning tools.

Tools:
    - BanditTool: Python SAST scanner
    - SafetyTool: Python dependency vulnerability scanner
    - TrivyTool: Container and IaC scanner
    - GitHubTool: GitHub API client for PR integration
"""

__version__ = "1.0.0"

from .bandit_tool import BanditTool
from .safety_tool import SafetyTool
from .trivy_tool import TrivyTool
from .github_tool import GitHubTool

__all__ = [
    "BanditTool",
    "SafetyTool",
    "TrivyTool",
    "GitHubTool",
]
