# System Architecture — BuildTrust AI

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    subgraph Client Tier
        UI[React Enterprise Dashboard\nTypeScript + Vite + Tailwind]
        CLI[CI/CD CLI / Developer Client\nPowerShell / cURL]
    end

    subgraph Application Tier [AWS App Runner / Local FastAPI]
        API[FastAPI Application Gateway\n/api/v1 prefix]
        AUTH[JWT & Role Authorization\nADMIN | DEVELOPER | VIEWER]
        INGEST[Evidence Ingestion & Deduplication]
        
        subgraph ECTE Core [Evidence-Change Trust Engine]
            VERIF[Artifact Verifier\nStreaming SHA-256]
            SBOM_A[CycloneDX SBOM Analyzer]
            OSV_S[Vulnerability Service\nOSV.dev + Offline Fallback]
            PROV_V[SLSA / in-toto Provenance Verifier]
            TEST_A[Test Suite Analyzer]
            ML[IsolationForest Anomaly Model\nscikit-learn]
            POL[Deterministic Policy Gate]
        end

        SSE[Server-Sent Events Broadcaster]
    end

    subgraph Storage Tier
        DYNAMO[(Amazon DynamoDB\nBuildTrustRecords Single-Table)]
        S3[(Amazon S3\nEncrypted Evidence & Artifact Vault)]
        LOCAL[(Local JSON/SQLite Storage\nbackend/data)]
    end

    subgraph External Services
        OSV[OSV.dev API\nOpen Source Vulnerability Database]
    end

    UI -->|REST API Requests| API
    UI <---|SSE Live Event Stream| SSE
    CLI -->|Submit Manifest & Artifacts| API

    API --> AUTH
    AUTH --> INGEST
    INGEST --> VERIF
    INGEST --> SBOM_A
    INGEST --> OSV_S
    INGEST --> PROV_V
    INGEST --> TEST_A

    OSV_S -->|Query Vulnerabilities| OSV

    VERIF & SBOM_A & OSV_S & PROV_V & TEST_A --> ML
    VERIF & SBOM_A & OSV_S & PROV_V & TEST_A & ML --> POL

    POL -->|Assessment Result| INGEST
    INGEST -->|Persist Metadata & Events| DYNAMO
    INGEST -->|Store Binary Artifacts| S3
    INGEST -.->|Local Mode Persistence| LOCAL
    INGEST -->|Publish Assessment Changed| SSE
```

---

## 2. Component Descriptions

### 2.1 Presentation Tier
- **Framework:** React 18 with TypeScript, bundled using Vite.
- **Styling & UI:** Tailwind CSS with enterprise cybersecurity theme.
- **Visualization:** Recharts (bar charts, status distributions) and Lucide React icons.
- **Live Updates:** `useLiveEvents` hook connecting to `/api/v1/events` via `EventSource`, with automatic 5-second polling fallback if disconnected.

### 2.2 Application & Business Logic Tier
- **Framework:** Python 3.11 with FastAPI and Uvicorn.
- **Configuration:** Pydantic BaseSettings loading `.env` with validation.
- **Authentication:** JWT Bearer tokens signed with HMAC-SHA256 and bcrypt password hashing.
- **Repository Abstraction:** `BaseRepository` interface implemented by `LocalRepository` (for offline zero-dependency development) and `DynamoDBRepository` + `S3Repository` (for AWS cloud deployment).

### 2.3 Cloud Persistence Tier (AWS)
- **Amazon DynamoDB:** Single-table design (`BuildTrustRecords`) with Partition Key `PK` and Sort Key `SK`.
- **Amazon S3:** Server-side AES256 encrypted bucket (`buildtrust-vault-<account>-<env>`) storing release binaries, CycloneDX documents, and provenance files.
- **AWS App Runner:** Containerized FastAPI service hosted with attached IAM instance role.
- **Amazon CloudWatch:** Structured JSON audit logging under `/aws/apprunner/buildtrust-ai-<env>`.
