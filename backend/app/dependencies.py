import os
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.app.config import settings
from backend.app.repositories.base import BaseRepository
from backend.app.repositories.local_repository import LocalRepository
from backend.app.repositories.dynamodb_repository import DynamoDBRepository
from backend.app.repositories.s3_repository import S3Repository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# Singleton repository instances
_local_repo: Optional[LocalRepository] = None
_dynamo_repo: Optional[DynamoDBRepository] = None
_s3_repo: Optional[S3Repository] = None

def get_repository() -> BaseRepository:
    """Dependency provider returning the configured storage repository."""
    global _local_repo, _dynamo_repo
    if settings.STORAGE_BACKEND == "aws":
        if not settings.DYNAMODB_TABLE_NAME:
            raise RuntimeError("STORAGE_BACKEND is 'aws' but DYNAMODB_TABLE_NAME is not configured.")
        if _dynamo_repo is None:
            _dynamo_repo = DynamoDBRepository(
                table_name=settings.DYNAMODB_TABLE_NAME,
                region_name=settings.AWS_REGION
            )
        return _dynamo_repo
    else:
        if _local_repo is None:
            _local_repo = LocalRepository(storage_dir=settings.LOCAL_STORAGE_DIR)
        return _local_repo

def get_s3_repository() -> Optional[S3Repository]:
    """Dependency provider returning S3 repository if configured."""
    global _s3_repo
    if settings.STORAGE_BACKEND == "aws" and settings.S3_BUCKET_NAME:
        if _s3_repo is None:
            _s3_repo = S3Repository(
                bucket_name=settings.S3_BUCKET_NAME,
                region_name=settings.AWS_REGION
            )
        return _s3_repo
    return None

def init_bootstrap_admin(repo: BaseRepository):
    """Seed initial administrator account if no users exist."""
    admin_user = repo.get_user_by_email(settings.INITIAL_ADMIN_EMAIL)
    if not admin_user:
        hashed = get_password_hash(settings.INITIAL_ADMIN_PASSWORD)
        repo.save_user({
            "email": settings.INITIAL_ADMIN_EMAIL.lower(),
            "full_name": "BuildTrust System Administrator",
            "hashed_password": hashed,
            "role": settings.INITIAL_ADMIN_ROLE,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    repo: BaseRepository = Depends(get_repository)
) -> Dict[str, Any]:
    """Authenticate caller via Bearer JWT token."""
    init_bootstrap_admin(repo)

    if not credentials:
        # For public demo evaluation mode, if no token is provided in local dev,
        # return a default guest viewer or require auth. Here we enforce secure token authentication.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims: missing subject.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = repo.get_user_by_email(email)
    if user is None or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_roles(allowed_roles: List[str]):
    """Role-based authorization dependency factory."""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role", "VIEWER")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the roles: {allowed_roles}. Current role: {user_role}."
            )
        return current_user
    return role_checker
