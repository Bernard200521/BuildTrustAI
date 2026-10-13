import pytest
from backend.app.dependencies import verify_password, get_password_hash, create_access_token
from backend.app.repositories.local_repository import LocalRepository

def test_password_hashing_and_verification():
    raw_pass = "SuperSecureReleasePass123!"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_generation():
    token = create_access_token(data={"sub": "dev@buildtrust.ai", "role": "DEVELOPER"})
    assert isinstance(token, str)
    assert len(token) > 20
