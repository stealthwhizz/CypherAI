"""
Cypher AI Demo Script
=====================

This script demonstrates the full workflow of the multi-agent security scanning system.

Usage:
    python demo/run_demo.py

Features Demonstrated:
- Multi-agent coordination
- Security vulnerability detection
- Compliance validation
- Performance monitoring
- Risk scoring and decision making
- Report generation
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.orchestrator import RootOrchestrator
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init(autoreset=True)


def print_banner():
    """Print the Cypher AI banner."""
    banner = f"""
{Fore.CYAN}{'=' * 80}
{Fore.CYAN}   ____                    _                       _    ___ 
{Fore.CYAN}  / ___|   _   _   _ __   | |__     ___   _ __   / \\  |_ _|
{Fore.CYAN} | |      | | | | | '_ \\  | '_ \\   / _ \\ | '__| / _ \\  | | 
{Fore.CYAN} | |___   | |_| | | |_) | | | | | |  __/ | |   / ___ \\ | | 
{Fore.CYAN}  \\____|   \\__, | | .__/  |_| |_|  \\___| |_|  /_/   \\_\\___|
{Fore.CYAN}           |___/  |_|                                        
{Fore.CYAN}
{Fore.YELLOW}           Multi-Agent DevSecOps Security Automation
{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}
"""
    print(banner)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Fore.YELLOW}{'─' * 80}")
    print(f"{Fore.YELLOW}► {title}")
    print(f"{Fore.YELLOW}{'─' * 80}{Style.RESET_ALL}\n")


def print_finding(severity: str, message: str, indent: int = 0):
    """Print a security finding with color coding."""
    colors = {
        "CRITICAL": Fore.RED,
        "HIGH": Fore.RED,
        "MEDIUM": Fore.YELLOW,
        "LOW": Fore.BLUE,
        "INFO": Fore.CYAN
    }
    
    icons = {
        "CRITICAL": "❌",
        "HIGH": "⚠️",
        "MEDIUM": "⚠️",
        "LOW": "ℹ️",
        "INFO": "ℹ️"
    }
    
    color = colors.get(severity, Fore.WHITE)
    icon = icons.get(severity, "•")
    prefix = "  " * indent
    
    print(f"{prefix}{color}{icon} {severity}: {message}{Style.RESET_ALL}")


def print_success(message: str):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}")


def run_demo():
    """Run the full demo workflow."""
    print_banner()
    
    print_section("Demo Overview")
    print_info("This demo will scan the vulnerable code files in the demo/ directory")
    print_info("The multi-agent system will detect various security issues:")
    print("  • SQL Injection vulnerabilities")
    print("  • Hardcoded secrets and credentials")
    print("  • Vulnerable dependencies")
    print("  • PCI DSS compliance violations")
    print("  • Performance anti-patterns (N+1 queries)")
    print("  • And more...")
    
    input(f"\n{Fore.GREEN}Press Enter to start the scan...{Style.RESET_ALL}")
    
    # Setup demo files
    print_section("Setup")
    demo_dir = Path(__file__).parent
    vulnerable_file = demo_dir / "vulnerable_code.py"
    requirements_file = demo_dir / "requirements_vuln.txt"
    
    if not vulnerable_file.exists():
        print_error(f"Demo file not found: {vulnerable_file}")
        return
    
    print_success(f"Found vulnerable code: {vulnerable_file}")
    print_success(f"Found requirements file: {requirements_file}")
    
    # Prepare PR data
    pr_data = {
        "pr_number": 123,
        "title": "Demo: Testing Cypher AI Security Scanner",
        "author": "demo-user",
        "branch": "feature/demo-vulnerabilities",
        "files_changed": [
            str(vulnerable_file),
            str(requirements_file)
        ],
        "additions": 250,
        "deletions": 10
    }
    
    print_info(f"Simulating PR #{pr_data['pr_number']}: {pr_data['title']}")
    print_info(f"Files to scan: {len(pr_data['files_changed'])}")
    
    # Initialize orchestrator
    print_section("Initializing Multi-Agent System")
    try:
        print_info("Loading Root Orchestrator Agent...")
        orchestrator = RootOrchestrator()
        print_success("Root Orchestrator initialized")
        
        print_info("Loading Specialist Agents:")
        print("  • Security Scanner Agent")
        print("  • Compliance Enforcer Agent")
        print("  • Performance Monitor Agent")
        print("  • Policy Engine Agent")
        print_success("All agents initialized and ready")
        
    except Exception as e:
        print_error(f"Failed to initialize agents: {e}")
        print_info("Make sure you have set GOOGLE_API_KEY in your .env file")
        return
    
    # Run analysis
    print_section("Running Multi-Agent Security Scan")
    print_info("Orchestrator delegating tasks to specialist agents...")
    
    try:
        start_time = datetime.now()
        
        # Run the analysis
        results = orchestrator.analyze_pr(pr_data)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print_success(f"Scan completed in {duration:.2f} seconds")
        
    except Exception as e:
        print_error(f"Scan failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Display results
    print_section("Security Findings")
    
    findings = results.get("findings", {})
    
    # Security findings
    security_findings = findings.get("security", [])
    if security_findings:
        print(f"{Fore.CYAN}[Security Scanner Agent] Found {len(security_findings)} issue(s):{Style.RESET_ALL}")
        for finding in security_findings[:10]:  # Show first 10
            print_finding(
                finding.get("severity", "UNKNOWN"),
                f"{finding.get('title', 'Unknown')} at {finding.get('location', 'unknown location')}",
                indent=1
            )
        if len(security_findings) > 10:
            print(f"  ... and {len(security_findings) - 10} more")
    
    # Compliance findings
    compliance_findings = findings.get("compliance", [])
    if compliance_findings:
        print(f"\n{Fore.CYAN}[Compliance Enforcer Agent] Found {len(compliance_findings)} violation(s):{Style.RESET_ALL}")
        for finding in compliance_findings[:10]:
            print_finding(
                finding.get("severity", "UNKNOWN"),
                f"{finding.get('title', 'Unknown')} - {finding.get('framework', 'Unknown framework')}",
                indent=1
            )
    
    # Performance findings
    performance_findings = findings.get("performance", [])
    if performance_findings:
        print(f"\n{Fore.CYAN}[Performance Monitor Agent] Found {len(performance_findings)} issue(s):{Style.RESET_ALL}")
        for finding in performance_findings:
            print_finding(
                finding.get("severity", "UNKNOWN"),
                finding.get("title", "Unknown"),
                indent=1
            )
    
    # Summary
    print_section("Risk Assessment")
    
    summary = results.get("summary", {})
    risk_score = summary.get("risk_score", 0)
    severity_breakdown = summary.get("severity_breakdown", {})
    
    print(f"Overall Risk Score: {Fore.RED if risk_score > 70 else Fore.YELLOW if risk_score > 40 else Fore.GREEN}{risk_score}/100{Style.RESET_ALL}")
    print("\nSeverity Breakdown:")
    print(f"  {Fore.RED}• Critical: {severity_breakdown.get('CRITICAL', 0)}{Style.RESET_ALL}")
    print(f"  {Fore.RED}• High: {severity_breakdown.get('HIGH', 0)}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}• Medium: {severity_breakdown.get('MEDIUM', 0)}{Style.RESET_ALL}")
    print(f"  {Fore.BLUE}• Low: {severity_breakdown.get('LOW', 0)}{Style.RESET_ALL}")
    
    # Decision
    print_section("Merge Decision")
    
    decision = results.get("decision", "UNKNOWN")
    reason = results.get("reason", "No reason provided")
    
    if decision == "BLOCK":
        print_error(f"🚫 MERGE BLOCKED")
        print(f"{Fore.RED}Reason: {reason}{Style.RESET_ALL}")
    elif decision == "APPROVE":
        print_success("✅ MERGE APPROVED")
        print(f"{Fore.GREEN}Reason: {reason}{Style.RESET_ALL}")
    else:
        print_info(f"⚠️ REVIEW REQUIRED")
        print(f"{Fore.YELLOW}Reason: {reason}{Style.RESET_ALL}")
    
    # Save report
    print_section("Report Generation")
    
    report_path = results.get("report_path")
    if report_path:
        print_success(f"Full report saved to: {report_path}")
        print_info("The report includes:")
        print("  • Detailed vulnerability descriptions")
        print("  • Code snippets showing issues")
        print("  • Remediation guidance")
        print("  • Compliance mapping")
    
    # Demo complete
    print_section("Demo Complete")
    print_success("Cypher AI successfully detected multiple security issues!")
    print_info("Next steps:")
    print("  1. Review the generated report")
    print("  2. Fix the identified vulnerabilities")
    print("  3. Re-run the scan to verify fixes")
    print("  4. Integrate with your CI/CD pipeline")
    
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{Fore.RED}Demo failed with error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
