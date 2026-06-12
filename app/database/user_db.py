import json
import os
from typing import Optional, Dict

from app.config import USERS_FILE_PATH


def _load_users() -> Dict:
    if not os.path.exists(USERS_FILE_PATH):
        return {}
    
    # Fix: handle empty file
    with open(USERS_FILE_PATH, "r") as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)


def _save_users(users: Dict):
    os.makedirs(os.path.dirname(USERS_FILE_PATH), exist_ok=True)
    with open(USERS_FILE_PATH, "w") as f:
        json.dump(users, f, indent=2)


def get_user_by_username(username: str) -> Optional[Dict]:
    users = _load_users()
    return users.get(username)


def get_user_by_id(user_id: str) -> Optional[Dict]:
    users = _load_users()
    for user in users.values():
        if user["user_id"] == user_id:
            return user
    return None


def save_new_user(user_id: str, username: str, hashed_password: str):
    users = _load_users()
    users[username] = {
        "user_id": user_id,
        "username": username,
        "hashed_password": hashed_password
    }
    _save_users(users)


def username_exists(username: str) -> bool:
    users = _load_users()
    return username in users