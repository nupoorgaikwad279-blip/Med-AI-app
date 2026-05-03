import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

USERS_FILE = 'users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
        
    hashed_password = generate_password_hash(password)
    users[username] = {
        "password": hashed_password, 
        "history": [],
        "profile": {},
        "records": []
    }
    save_users(users)
    return True, "Registration successful."

def authenticate(username, password):
    users = load_users()
    
    if username == "admin" and password == "admin":
        return True
        
    if username in users:
        stored_hash = users[username]["password"]
        if check_password_hash(stored_hash, password):
            return True
    return False

def add_history(username, query):
    if username == "admin": return # Skip for dummy admin
    users = load_users()
    if username in users:
        if "history" not in users[username]:
            users[username]["history"] = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[username]["history"].append({"query": query, "time": timestamp})
        save_users(users)

def get_history(username):
    if username == "admin": return []
    users = load_users()
    if username in users:
        return users[username].get("history", [])
    return []

def get_user_profile(username):
    if username == "admin": return {}
    users = load_users()
    if username in users:
        return users[username].get("profile", {})
    return {}

def update_user_profile(username, profile_data):
    if username == "admin": return False
    users = load_users()
    if username in users:
        users[username]["profile"] = profile_data
        save_users(users)
        return True
    return False

def add_record(username, record):
    if username == "admin": return
    users = load_users()
    if username in users:
        if "records" not in users[username]:
            users[username]["records"] = []
        users[username]["records"].append(record)
        save_users(users)

def get_records(username):
    if username == "admin": return []
    users = load_users()
    if username in users:
        return users[username].get("records", [])
    return []

