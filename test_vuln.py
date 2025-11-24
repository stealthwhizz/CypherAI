import os

# SQL Injection
def search_user(name):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    return db.execute(query)

# Hardcoded Secret
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"

# Eval injection
def run_code(user_input):
    eval(user_input)
