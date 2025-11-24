"""
Cypher AI Webhook Server
=========================

Flask server for receiving GitHub webhook events.

This server:
- Receives GitHub pull request events
- Verifies webhook signatures
- Triggers security scans via the orchestrator
- Posts results back to GitHub as PR comments

Usage:
    python webhook_server.py
    
Or:
    python main.py --server
"""

import os
import hmac
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from agents.orchestrator import RootOrchestrator
from tools.github_tool import GitHubTool

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Initialize tools
orchestrator = None
github_tool = None


def verify_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature.
    
    Args:
        payload: Request body bytes
        signature: X-Hub-Signature-256 header value
    
    Returns:
        True if signature is valid
    """
    if not WEBHOOK_SECRET:
        logger.warning("No webhook secret configured. Skipping signature verification.")
        return True
    
    if not signature:
        return False
    
    # Signature format: sha256=<hash>
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = signature.split("=")[1]
    
    # Calculate HMAC
    mac = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    )
    
    return hmac.compare_digest(mac.hexdigest(), expected_signature)


def extract_pr_data(event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract relevant PR data from webhook event.
    
    Args:
        event_data: GitHub webhook event data
    
    Returns:
        Processed PR data or None
    """
    try:
        action = event_data.get("action")
        
        # Only process opened, reopened, and synchronize events
        if action not in ["opened", "reopened", "synchronize"]:
            logger.info(f"Ignoring PR action: {action}")
            return None
        
        pr = event_data.get("pull_request", {})
        repo = event_data.get("repository", {})
        
        pr_data = {
            "pr_number": pr.get("number"),
            "title": pr.get("title"),
            "author": pr.get("user", {}).get("login"),
            "branch": pr.get("head", {}).get("ref"),
            "base_branch": pr.get("base", {}).get("ref"),
            "sha": pr.get("head", {}).get("sha"),
            "repo_owner": repo.get("owner", {}).get("login"),
            "repo_name": repo.get("name"),
            "repo_full_name": repo.get("full_name"),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "changed_files": pr.get("changed_files", 0),
            "files_changed": []  # Will be populated by fetching PR files
        }
        
        return pr_data
        
    except Exception as e:
        logger.error(f"Error extracting PR data: {e}")
        return None


def fetch_pr_files(pr_data: Dict[str, Any]) -> list:
    """
    Fetch list of changed files from GitHub API.
    
    Args:
        pr_data: PR metadata
    
    Returns:
        List of file paths
    """
    try:
        if not github_tool:
            logger.error("GitHub tool not initialized")
            return []
        
        owner = pr_data.get("repo_owner")
        repo = pr_data.get("repo_name")
        pr_number = pr_data.get("pr_number")
        
        if not all([owner, repo, pr_number]):
            logger.error("Missing PR information")
            return []
        
        files = github_tool.get_pr_files(owner, repo, pr_number)
        
        # Extract file paths
        file_paths = [f.get("filename") for f in files if f.get("filename")]
        
        logger.info(f"Fetched {len(file_paths)} changed files")
        return file_paths
        
    except Exception as e:
        logger.error(f"Error fetching PR files: {e}")
        return []


def process_pr_scan(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process PR security scan.
    
    Args:
        pr_data: PR metadata
    
    Returns:
        Scan results
    """
    try:
        logger.info(f"Starting scan for PR #{pr_data.get('pr_number')}")
        
        # Fetch changed files
        pr_data["files_changed"] = fetch_pr_files(pr_data)
        
        if not pr_data["files_changed"]:
            logger.warning("No files to scan")
            return {
                "decision": "APPROVE",
                "reason": "No files changed",
                "summary": {"total_findings": 0}
            }
        
        # Run security scan
        results = orchestrator.analyze_pr(pr_data)
        
        logger.info(f"Scan complete for PR #{pr_data.get('pr_number')}: {results.get('decision')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing PR scan: {e}")
        return {
            "decision": "ERROR",
            "reason": f"Scan failed: {str(e)}",
            "summary": {"total_findings": 0}
        }


def post_results_to_github(pr_data: Dict[str, Any], results: Dict[str, Any]) -> bool:
    """
    Post scan results to GitHub PR.
    
    Args:
        pr_data: PR metadata
        results: Scan results
    
    Returns:
        True if successful
    """
    try:
        if not github_tool:
            logger.error("GitHub tool not initialized")
            return False
        
        owner = pr_data.get("repo_owner")
        repo = pr_data.get("repo_name")
        pr_number = pr_data.get("pr_number")
        sha = pr_data.get("sha")
        
        # Post comment with findings
        comment = github_tool.format_findings_comment(
            findings=results.get("findings", {}),
            summary=results.get("summary", {}),
            decision=results.get("decision", "UNKNOWN"),
            format_type="table"
        )
        
        github_tool.post_comment(owner, repo, pr_number, comment)
        
        # Update commit status
        decision = results.get("decision")
        if decision == "APPROVE":
            state = "success"
            description = "Security scan passed"
        elif decision == "BLOCK":
            state = "failure"
            description = "Security issues found"
        else:
            state = "pending"
            description = "Manual review required"
        
        github_tool.update_status(
            owner, repo, sha, state, description
        )
        
        logger.info(f"Posted results to GitHub for PR #{pr_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error posting to GitHub: {e}")
        return False


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle GitHub webhook events."""
    try:
        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse event
        event_type = request.headers.get("X-GitHub-Event")
        event_data = request.get_json()
        
        logger.info(f"Received webhook event: {event_type}")
        
        # Only process pull_request events
        if event_type != "pull_request":
            return jsonify({"message": "Event ignored"}), 200
        
        # Extract PR data
        pr_data = extract_pr_data(event_data)
        if not pr_data:
            return jsonify({"message": "PR action ignored"}), 200
        
        logger.info(f"Processing PR #{pr_data.get('pr_number')}: {pr_data.get('title')}")
        
        # Process scan (could be async in production)
        results = process_pr_scan(pr_data)
        
        # Post results to GitHub
        if GITHUB_TOKEN:
            post_results_to_github(pr_data, results)
        else:
            logger.warning("No GitHub token configured. Skipping result posting.")
        
        return jsonify({
            "message": "Scan completed",
            "decision": results.get("decision"),
            "findings": results.get("summary", {}).get("total_findings", 0)
        }), 200
        
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Cypher AI Webhook Server",
        "version": "1.0.0"
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint."""
    return jsonify({
        "service": "Cypher AI Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "/webhook": "POST - GitHub webhook handler",
            "/health": "GET - Health check",
            "/": "GET - Service information"
        }
    }), 200


def initialize():
    """Initialize global objects."""
    global orchestrator, github_tool
    
    logger.info("Initializing Cypher AI Webhook Server...")
    
    # Initialize orchestrator
    logger.info("Loading orchestrator...")
    orchestrator = RootOrchestrator()
    
    # Initialize GitHub tool
    if GITHUB_TOKEN:
        logger.info("Initializing GitHub tool...")
        github_tool = GitHubTool(GITHUB_TOKEN)
    else:
        logger.warning("No GitHub token configured. GitHub integration disabled.")
    
    logger.info("Initialization complete")


def main():
    """Main entry point."""
    initialize()
    
    # Get configuration from environment
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"
    
    logger.info(f"Starting server on {host}:{port}")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
