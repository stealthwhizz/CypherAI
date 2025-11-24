"""
Vulnerable Code Demo File
==========================

This file contains intentional security vulnerabilities for testing Cypher AI.

WARNING: This code is deliberately insecure for demonstration purposes.
         DO NOT use any of these patterns in production code!

Testing Coverage:
- SQL Injection (CWE-89)
- Hardcoded Secrets (CWE-798)
- Command Injection (CWE-78)
- Cross-Site Scripting (CWE-79)
- Insecure Deserialization (CWE-502)
- N+1 Query Pattern
- Weak Cryptography (CWE-327)
- Path Traversal (CWE-22)
"""

import os
import pickle
import hashlib
from typing import List, Dict, Any


# ============================================================================
# CRITICAL: SQL Injection Vulnerabilities
# ============================================================================

def search_users(username: str) -> List[Dict[str, Any]]:
    """
    Search for users by username.
    
    VULNERABILITY: SQL Injection (CWE-89) - PCI DSS 6.5.1
    Severity: CRITICAL
    """
    # String formatting allows SQL injection
    query = f"SELECT * FROM users WHERE name = '{username}'"
    return db.execute(query)


def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user by ID.
    
    VULNERABILITY: SQL Injection (CWE-89)
    Severity: CRITICAL
    """
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)


def login_user(username: str, password: str) -> bool:
    """
    Authenticate user.
    
    VULNERABILITY: SQL Injection (CWE-89)
    Severity: CRITICAL
    """
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return len(result) > 0


# ============================================================================
# CRITICAL: Hardcoded Secrets
# ============================================================================

# AWS Credentials - CRITICAL VULNERABILITY (CWE-798)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# API Keys - HIGH VULNERABILITY (CWE-798)
STRIPE_API_KEY = "stripe_key_intentionally_fake_for_demo_purposes"  # DEMO ONLY - NOT A REAL KEY
GITHUB_TOKEN = "github_token_intentionally_fake_demo_value"  # DEMO ONLY - NOT A REAL KEY
API_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example"

# Database Credentials - CRITICAL VULNERABILITY (CWE-798) - PCI DSS 3.4
DATABASE_URL = "postgresql://admin:password123@localhost:5432/testdb"  # DEMO ONLY
MONGODB_URI = "mongodb://root:password123@localhost:27017/testdb"  # DEMO ONLY

# Encryption Keys - CRITICAL VULNERABILITY (CWE-798)
SECRET_KEY = "my-super-secret-key-12345"
ENCRYPTION_KEY = "0123456789abcdef0123456789abcdef"


# ============================================================================
# HIGH: Command Injection Vulnerabilities
# ============================================================================

def ping_server(hostname: str) -> str:
    """
    Ping a server to check connectivity.
    
    VULNERABILITY: Command Injection (CWE-78)
    Severity: HIGH
    """
    command = f"ping -c 4 {hostname}"
    result = os.system(command)
    return result


def backup_files(filename: str) -> None:
    """
    Backup files to archive.
    
    VULNERABILITY: Command Injection (CWE-78)
    Severity: HIGH
    """
    os.system(f"tar -czf backup.tar.gz {filename}")


# ============================================================================
# HIGH: Path Traversal Vulnerabilities
# ============================================================================

def read_file(filename: str) -> str:
    """
    Read file contents.
    
    VULNERABILITY: Path Traversal (CWE-22)
    Severity: HIGH
    """
    # No sanitization allows directory traversal
    with open(f"/var/www/uploads/{filename}", "r") as f:
        return f.read()


def serve_static_file(file_path: str) -> bytes:
    """
    Serve static file to user.
    
    VULNERABILITY: Path Traversal (CWE-22)
    Severity: HIGH
    """
    with open(file_path, "rb") as f:
        return f.read()


# ============================================================================
# MEDIUM: Weak Cryptography
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash user password for storage.
    
    VULNERABILITY: Weak Cryptography (CWE-327) - PCI DSS 6.5.3
    Severity: MEDIUM
    """
    # MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data.
    
    VULNERABILITY: Weak Cryptography (CWE-327)
    Severity: MEDIUM
    """
    # Weak XOR encryption
    key = 42
    return ''.join(chr(ord(c) ^ key) for c in data)


# ============================================================================
# HIGH: Insecure Deserialization
# ============================================================================

def load_user_session(session_data: bytes) -> Dict[str, Any]:
    """
    Deserialize user session data.
    
    VULNERABILITY: Insecure Deserialization (CWE-502)
    Severity: HIGH
    """
    # Pickle can execute arbitrary code
    return pickle.loads(session_data)


def restore_object(serialized: str) -> Any:
    """
    Restore object from serialized string.
    
    VULNERABILITY: Insecure Deserialization (CWE-502)
    Severity: HIGH
    """
    import yaml
    # yaml.load() is unsafe
    return yaml.load(serialized)


# ============================================================================
# MEDIUM: Cross-Site Scripting (XSS)
# ============================================================================

def render_user_profile(username: str) -> str:
    """
    Render user profile HTML.
    
    VULNERABILITY: XSS (CWE-79) - PCI DSS 6.5.7
    Severity: MEDIUM
    """
    # Unescaped user input in HTML
    return f"<div>Welcome, {username}!</div>"


def display_comment(comment: str) -> str:
    """
    Display user comment.
    
    VULNERABILITY: XSS (CWE-79)
    Severity: MEDIUM
    """
    html = f"""
    <div class="comment">
        <p>{comment}</p>
    </div>
    """
    return html


# ============================================================================
# MEDIUM: Performance Anti-Pattern - N+1 Queries
# ============================================================================

class User:
    """Mock User model."""
    pass


class Order:
    """Mock Order model."""
    pass


def get_user_orders_bad() -> List[Dict[str, Any]]:
    """
    Get all users with their orders.
    
    VULNERABILITY: N+1 Query Pattern
    Severity: MEDIUM (Performance)
    """
    users = User.query.all()
    result = []
    
    # N+1 query - fetches orders for each user individually
    for user in users:
        orders = Order.query.filter_by(user_id=user.id).all()
        result.append({
            'user': user,
            'orders': orders
        })
    
    return result


def get_user_posts_bad(user_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Get posts for multiple users.
    
    VULNERABILITY: N+1 Query Pattern
    Severity: MEDIUM (Performance)
    """
    posts = []
    for user_id in user_ids:
        # Database query inside loop
        user_posts = db.query(f"SELECT * FROM posts WHERE user_id = {user_id}")
        posts.extend(user_posts)
    
    return posts


# ============================================================================
# LOW: Insecure Random Number Generation
# ============================================================================

import random

def generate_session_token() -> str:
    """
    Generate session token for user.
    
    VULNERABILITY: Weak Random (CWE-338)
    Severity: LOW
    """
    # random.random() is not cryptographically secure
    return str(random.randint(1000000, 9999999))


def create_password_reset_token() -> str:
    """
    Create password reset token.
    
    VULNERABILITY: Weak Random (CWE-338)
    Severity: LOW
    """
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ''.join(random.choice(chars) for _ in range(20))


# ============================================================================
# MEDIUM: Information Disclosure
# ============================================================================

def get_user_profile(user_id: int) -> Dict[str, Any]:
    """
    Get user profile with sensitive information.
    
    VULNERABILITY: Information Disclosure (CWE-200)
    Severity: MEDIUM
    """
    try:
        user = db.get_user(user_id)
        return user
    except Exception as e:
        # Exposing stack traces to users
        return {"error": str(e), "stacktrace": traceback.format_exc()}


# ============================================================================
# Mock Database Class (for demonstration)
# ============================================================================

class MockDatabase:
    """Mock database for demonstration purposes."""
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        print(f"Executing: {query}")
        return []
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query."""
        return self.execute(sql)
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID."""
        return {"id": user_id, "name": "Test User"}


# Global database instance
db = MockDatabase()


# ============================================================================
# Main Function
# ============================================================================

if __name__ == "__main__":
    print("This file contains intentional vulnerabilities for testing.")
    print("DO NOT use any code from this file in production!")
