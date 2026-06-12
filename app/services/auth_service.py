import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS
from app.database.user_db import (
    get_user_by_username,
    save_new_user,
    username_exists
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "sub": user_id,
        "username": username,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def register_user(username: str, password: str) -> dict:
    if username_exists(username):
        return {"error": "Username already exists."}

    user_id = str(uuid.uuid4())
    hashed = hash_password(password)
    save_new_user(user_id=user_id, username=username, hashed_password=hashed)

    token = create_access_token(user_id=user_id, username=username)
    return {"user_id": user_id, "username": username, "token": token}


def login_user(username: str, password: str) -> dict:
    user = get_user_by_username(username)

    if not user:
        return {"error": "Invalid username or password."}

    if not verify_password(password, user["hashed_password"]):
        return {"error": "Invalid username or password."}

    token = create_access_token(user_id=user["user_id"], username=user["username"])
    return {"user_id": user["user_id"], "username": user["username"], "token": token}