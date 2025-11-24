"""
Cypher AI Main Entry Point
===========================

CLI interface for the multi-agent security scanning system.

Usage:
    python main.py --demo                    # Run demo with test files
    python main.py --scan FILE               # Scan specific file
    python main.py --scan-dir DIR            # Scan directory
    python main.py --server                  # Start webhook server
    python main.py --show-config             # Show configuration
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List
import json
import io

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    # Reconfigure stdout/stderr to use UTF-8
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import RootOrchestrator
from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv

# Initialize colorama for Windows compatibility
colorama_init(autoreset=True, strip=False)

# Load environment variables
load_dotenv()

# Setup logging
def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "cypher_ai.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)


def validate_environment() -> bool:
    """Check if required environment variables are set."""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print(f"{Fore.YELLOW}[!] Warning: GOOGLE_API_KEY not set{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  Running with limited functionality. Set API key in .env file.{Style.RESET_ALL}\n")
        return False
    
    if api_key == "test_key_for_demo":
        print(f"{Fore.YELLOW}[!] Using test API key - results may be simulated{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  For full functionality, get a real API key from: https://makersuite.google.com/app/apikey{Style.RESET_ALL}\n")
        return False
    
    return True


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


def scan_file(file_path: str) -> int:
    """
    Scan a single file.
    
    Args:
        file_path: Path to file to scan
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        print(f"\n{Fore.CYAN}Scanning file: {file_path}{Style.RESET_ALL}\n")
        
        orchestrator = RootOrchestrator()
        
        pr_data = {
            "pr_number": 0,
            "title": f"Scan: {Path(file_path).name}",
            "files_changed": [file_path]
        }
        
        results = orchestrator.analyze_pr(pr_data)
        
        print_results(results)
        
        return 0 if results["decision"] == "APPROVE" else 1
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        print(f"\n{Fore.RED}[X] File not found: {file_path}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  Please check the file path and try again.{Style.RESET_ALL}\n")
        return 1
    except Exception as e:
        logger.error(f"Error scanning file: {e}")
        print(f"\n{Fore.RED}[X] Scan failed: {e}{Style.RESET_ALL}\n")
        return 1


def scan_directory(dir_path: str) -> int:
    """
    Scan all files in a directory.
    
    Args:
        dir_path: Path to directory to scan
    
    Returns:
        Exit code
    """
    try:
        path = Path(dir_path)
        
        if not path.exists() or not path.is_dir():
            print(f"{Fore.RED}[X] Directory not found: {dir_path}{Style.RESET_ALL}")
            return 1
        
        # Find all Python files
        python_files = list(path.rglob("*.py"))
        requirements_files = list(path.rglob("requirements*.txt"))
        
        all_files = [str(f) for f in python_files + requirements_files]
        
        if not all_files:
            print(f"{Fore.YELLOW}[!] No Python or requirements files found in {dir_path}{Style.RESET_ALL}")
            return 0
        
        print(f"\n{Fore.CYAN}Scanning directory: {dir_path}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Found {len(all_files)} file(s) to scan{Style.RESET_ALL}\n")
        
        orchestrator = RootOrchestrator()
        
        pr_data = {
            "pr_number": 0,
            "title": f"Scan: {path.name}",
            "files_changed": all_files
        }
        
        results = orchestrator.analyze_pr(pr_data)
        
        print_results(results)
        
        return 0 if results["decision"] == "APPROVE" else 1
        
    except Exception as e:
        logger.error(f"Error scanning directory: {e}")
        print(f"\n{Fore.RED}[X] Scan failed: {e}{Style.RESET_ALL}\n")
        return 1


def run_demo() -> int:
    """
    Run the demo with test vulnerable files.
    
    Returns:
        Exit code
    """
    try:
        demo_script = Path("demo/run_demo.py")
        
        if demo_script.exists():
            # Run the dedicated demo script
            import subprocess
            result = subprocess.run([sys.executable, str(demo_script)], check=False)
            return result.returncode
        else:
            # Fallback: run basic demo
            print(f"{Fore.YELLOW}Demo script not found. Running basic scan...{Style.RESET_ALL}\n")
            
            demo_files = [
                "demo/vulnerable_code.py",
                "demo/requirements_vuln.txt"
            ]
            
            # Filter existing files
            existing_files = [f for f in demo_files if Path(f).exists()]
            
            if not existing_files:
                print(f"{Fore.RED}[X] No demo files found{Style.RESET_ALL}")
                return 1
            
            orchestrator = RootOrchestrator()
            
            pr_data = {
                "pr_number": 123,
                "title": "Demo: Testing Cypher AI",
                "files_changed": existing_files
            }
            
            results = orchestrator.analyze_pr(pr_data)
            print_results(results)
            
            return 0
            
    except Exception as e:
        logger.error(f"Error running demo: {e}")
        print(f"\n{Fore.RED}[X] Demo failed: {e}{Style.RESET_ALL}\n")
        return 1


def start_server() -> int:
    """
    Start the webhook server.
    
    Returns:
        Exit code
    """
    try:
        print(f"\n{Fore.CYAN}Starting Cypher AI webhook server...{Style.RESET_ALL}\n")
        
        import webhook_server
        webhook_server.main()
        
        return 0
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n{Fore.RED}[X] Server failed to start: {e}{Style.RESET_ALL}\n")
        return 1


def show_config() -> int:
    """
    Show current configuration.
    
    Returns:
        Exit code
    """
    try:
        import yaml
        
        config_path = Path("config/policies.yaml")
        
        if not config_path.exists():
            print(f"{Fore.RED}[X] Configuration file not found: {config_path}{Style.RESET_ALL}")
            return 1
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"\n{Fore.CYAN}Current Configuration{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        
        # Show key settings
        print(f"{Fore.YELLOW}Thresholds:{Style.RESET_ALL}")
        thresholds = config.get("thresholds", {})
        for key, value in thresholds.items():
            print(f"  {key}: {value}")
        
        print(f"\n{Fore.YELLOW}Enabled Compliance Frameworks:{Style.RESET_ALL}")
        compliance = config.get("compliance", {})
        for framework, settings in compliance.items():
            if settings.get("enabled"):
                print(f"  [+] {framework.upper()}")
        
        print(f"\n{Fore.YELLOW}Security Scanner:{Style.RESET_ALL}")
        scanner = config.get("security_scanner", {})
        for tool, settings in scanner.items():
            if isinstance(settings, dict) and settings.get("enabled"):
                print(f"  [+] {tool}")
        
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error showing config: {e}")
        print(f"\n{Fore.RED}[X] Failed to load config: {e}{Style.RESET_ALL}\n")
        return 1


def print_results(results: dict):
    """Print scan results in a formatted way."""
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}SCAN RESULTS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    summary = results.get("summary", {})
    decision = results.get("decision", "UNKNOWN")
    reason = results.get("reason", "")
    
    # Print summary
    print(f"{Fore.YELLOW}Risk Score:{Style.RESET_ALL} {summary.get('risk_score', 0)}/100")
    print(f"{Fore.YELLOW}Total Findings:{Style.RESET_ALL} {summary.get('total_findings', 0)}")
    print()
    
    # Print severity breakdown
    severity_breakdown = summary.get("severity_breakdown", {})
    print(f"{Fore.YELLOW}Severity Breakdown:{Style.RESET_ALL}")
    print(f"  {Fore.RED}Critical:{Style.RESET_ALL} {severity_breakdown.get('CRITICAL', 0)}")
    print(f"  {Fore.RED}High:{Style.RESET_ALL} {severity_breakdown.get('HIGH', 0)}")
    print(f"  {Fore.YELLOW}Medium:{Style.RESET_ALL} {severity_breakdown.get('MEDIUM', 0)}")
    print(f"  {Fore.BLUE}Low:{Style.RESET_ALL} {severity_breakdown.get('LOW', 0)}")
    print()
    
    # Print decision
    if decision == "APPROVE":
        print(f"{Fore.GREEN}[+] DECISION: APPROVED{Style.RESET_ALL}")
    elif decision == "BLOCK":
        print(f"{Fore.RED}[X] DECISION: BLOCKED{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}[!] DECISION: REVIEW REQUIRED{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}Reason:{Style.RESET_ALL} {reason}")
    print()
    
    # Print report location
    report_path = results.get("report_path")
    if report_path:
        print(f"{Fore.GREEN}[+] Report saved to:{Style.RESET_ALL} {report_path}")
    
    duration = results.get("duration", 0)
    print(f"{Fore.CYAN}Duration:{Style.RESET_ALL} {duration:.2f} seconds")
    
    print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Cypher AI - Multi-Agent DevSecOps Security Automation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo                        Run demo with test files
  python main.py --scan demo/vulnerable_code.py   Scan specific file
  python main.py --scan-dir ./src              Scan entire directory
  python main.py --server                      Start webhook server
  python main.py --show-config                 Show current configuration
        """
    )
    
    parser.add_argument('--demo', action='store_true', help='Run demo with test files')
    parser.add_argument('--scan', type=str, metavar='FILE', help='Scan specific file')
    parser.add_argument('--scan-dir', type=str, metavar='DIR', help='Scan directory')
    parser.add_argument('--server', action='store_true', help='Start webhook server')
    parser.add_argument('--show-config', action='store_true', help='Show configuration')
    parser.add_argument('--log-level', type=str, default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Print banner
    print_banner()
    
    # Validate environment for operations that need API key
    if args.demo or args.scan or args.scan_dir:
        validate_environment()
    
    # Execute command
    try:
        if args.demo:
            return run_demo()
        elif args.scan:
            return scan_file(args.scan)
        elif args.scan_dir:
            return scan_directory(args.scan_dir)
        elif args.server:
            return start_server()
        elif args.show_config:
            return show_config()
        else:
            parser.print_help()
            return 0
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n{Fore.RED}[X] Error: {e}{Style.RESET_ALL}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
