# API Documentation — BuildTrust AI

All endpoints use the prefix `/api/v1` and produce OpenAPI 3.0 documentation at `/docs` (Swagger UI) and `/redoc`.

---

## 1. Authentication (`/api/v1/auth`)

### 1.1 Login
- **Endpoint:** `POST /api/v1/auth/login`
- **Request Body:**
  ```json
  {
    "email": "admin@buildtrust.ai",
    "password": "BuildTrustAdmin2026!"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user": {
      "email": "admin@buildtrust.ai",
      "full_name": "BuildTrust System Administrator",
      "role": "ADMIN"
    }
  }
  ```

### 1.2 User Profile
- **Endpoint:** `GET /api/v1/auth/me`
- **Headers:** `Authorization: Bearer <token>`
- **Response:** `200 OK`

---

## 2. Projects & Releases (`/api/v1/projects`, `/api/v1/releases`)

### 2.1 Register Project
- **Endpoint:** `POST /api/v1/projects`
- **Role:** `ADMIN` or `DEVELOPER`
- **Request Body:**
  ```json
  {
    "project_id": "payment-gateway",
    "name": "Global Payment Gateway",
    "description": "PCI-DSS compliant payment processing service",
    "policy": {
      "approval_threshold": 85.0,
      "review_threshold": 60.0,
      "block_on_critical_vuln": true
    }
  }
  ```

### 2.2 Create Release Candidate
- **Endpoint:** `POST /api/v1/projects/{project_id}/releases`
- **Role:** `ADMIN` or `DEVELOPER`
- **Request Body:**
  ```json
  {
    "project_id": "payment-gateway",
    "release_id": "rel-payment-1.0.0",
    "version": "1.0.0",
    "source_commit": "a1b2c3d4e5f67890",
    "artifact": {
      "filename": "payment-service.zip",
      "expected_sha256": "ae4cb295b8a6d34680bede3714ee8ea7f69d65e148c7f7adedd56ac866a4abad"
    },
    "evidence_requirements": {
      "sbom_required": true,
      "provenance_required": true,
      "tests_required": true,
      "dependency_scan_required": true
    },
    "environment": "staging"
  }
  ```

---

## 3. Evidence & Verification (`/api/v1/releases/{release_id}/...`)

### 3.1 Direct Artifact Upload with Streaming SHA-256
- **Endpoint:** `POST /api/v1/releases/{release_id}/artifacts/upload`
- **Content-Type:** `multipart/form-data`
- **Description:** Streams binary file, computes real SHA-256, compares against expected hash, and automatically ingests `artifact_integrity` evidence.

### 3.2 Submit Evidence Envelope
- **Endpoint:** `POST /api/v1/releases/{release_id}/evidence`
- **Request Body:**
  ```json
  {
    "evidence_type": "vulnerability_scan",
    "source": "osv-scanner",
    "payload": {
      "scanner_name": "OSV-Scanner",
      "scan_timestamp": "2026-10-10T12:00:00Z",
      "total_findings": 0,
      "critical_count": 0,
      "high_count": 0,
      "medium_count": 0,
      "low_count": 0,
      "findings": []
    }
  }
  ```

---

## 4. Assessments & Dashboard (`/api/v1/releases/...`, `/api/v1/dashboard`)

### 4.1 Trigger Reassessment
- **Endpoint:** `POST /api/v1/releases/{release_id}/assessments`
- **Response:** `200 OK` (Returns versioned `AssessmentRecord`).

### 4.2 Dashboard Live Summary
- **Endpoint:** `GET /api/v1/dashboard/summary`
- **Response:** `200 OK` (Aggregated live metrics, vulnerability distribution, recent events).

### 4.3 Live Server-Sent Events (SSE) Stream
- **Endpoint:** `GET /api/v1/events`
- **Content-Type:** `text/event-stream`
- **Response:** Stream of real-time state change events.
