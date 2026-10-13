import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.config import settings

client = TestClient(app)

def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "storage_backend" in data

def test_readiness_check():
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"

def test_auth_login_and_me():
    # Login as bootstrapped admin
    login_resp = client.post("/api/v1/auth/login", json={
        "email": settings.INITIAL_ADMIN_EMAIL,
        "password": settings.INITIAL_ADMIN_PASSWORD
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token

    # Introspect me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"].lower() == settings.INITIAL_ADMIN_EMAIL.lower()

def test_dashboard_summary():
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert "vulnerability_distribution" in data
    assert "recent_events" in data
