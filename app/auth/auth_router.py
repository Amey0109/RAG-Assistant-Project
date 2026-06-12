from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.auth_service import register_user, login_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(request: AuthRequest):
    result = register_user(
        username=request.username,
        password=request.password
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/login")
def login(request: AuthRequest):
    result = login_user(
        username=request.username,
        password=request.password
    )
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    return result