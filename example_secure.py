"""
Sample production code for testing CypherAI security scanner
"""

def get_user_data(user_id):
    """Fetch user data from database."""
    import sqlite3
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Secure parameterized query
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result


def hash_password(password):
    """Hash password securely."""
    import hashlib
    
    # Use SHA256 instead of MD5
    return hashlib.sha256(password.encode()).hexdigest()


def process_config():
    """Load configuration from environment variables."""
    import os
    
    # Secure: Load from environment
    api_key = os.getenv('API_KEY')
    db_password = os.getenv('DB_PASSWORD')
    
    return {
        'api_key': api_key,
        'db_password': db_password
    }


if __name__ == "__main__":
    # Example usage
    user = get_user_data(123)
    hashed = hash_password("user_password")
    config = process_config()
    
    print("Secure code example")
