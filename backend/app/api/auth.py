from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from backend.app.dependencies import (
    get_repository,
    verify_password,
    create_access_token,
    get_current_user,
    init_bootstrap_admin
)
from backend.app.repositories.base import BaseRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, repo: BaseRepository = Depends(get_repository)):
    init_bootstrap_admin(repo)
    user = repo.get_user_by_email(request.email)
    if not user or not verify_password(request.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(data={"sub": user["email"], "role": user.get("role", "VIEWER")})
    user_info = {
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", "VIEWER"),
        "created_at": user.get("created_at")
    }
    return LoginResponse(access_token=token, user=user_info)

@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", "VIEWER"),
        "created_at": user.get("created_at")
    }
