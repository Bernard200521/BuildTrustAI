# BuildTrust AI — AI-Assisted Continuous Trust Verification for Secure Software Releases

> **An AI-Assisted Continuous Trust Verification and Risk-Adaptive Release Gate for Secure Software Supply Chains**  
> *Proposed Technical Contribution:* **Evidence-Change Trust Engine (ECTE)**  
> *Academic / Technical Mini-Project for Wipro Submission*

---

## 1. Overview & Four Engineering Domains

BuildTrust AI is a functional, full-stack prototype that unifies fragmented software supply chain evidence into an adaptive, continuously evaluated release gate.

```
       +-----------------------------------------------------------+
       |               React Enterprise Dashboard                  |
       |  (Overview, Explorer, Details, Live SSE, AI Panel, Audit) |
       +-----------------------------------------------------------+
                                     |
                  HTTP REST API & Server-Sent Events (SSE)
                                     v
       +-----------------------------------------------------------+
       |                  FastAPI Backend Gateway                  |
       |    +-------------------------------------------------+    |
       |    |     Evidence-Change Trust Engine (ECTE Core)    |    |
       |    |  • Streaming SHA-256 Digest Verifier            |    |
       |    |  • CycloneDX SBOM Component Analyzer            |    |
       |    |  • OSV.dev Continuous Vulnerability Engine       |    |
       |    |  • SLSA v1.0 & Cosign Provenance Verifier       |    |
       |    |  • scikit-learn IsolationForest Anomaly Model   |    |
       |    |  • Deterministic Security Policy Gate           |    |
       |    +-------------------------------------------------+    |
       +-----------------------------------------------------------+
                         |                           |
                 (Local Dev Mode)             (AWS Cloud Mode)
                         v                           v
              +---------------------+     +---------------------+
              | Local JSON Storage  |     | Amazon DynamoDB     |
              | & Local Artifacts   |     | Amazon S3 Vault     |
              +---------------------+     | Amazon CloudWatch   |
                                          +---------------------+
```

1. **Data Engineering:** Canonical evidence envelopes, deduplication via content SHA-256, schema validation, versioned assessment history, and repository abstraction (`LocalRepository` and `DynamoDBRepository` + `S3Repository`).
2. **Security Engineering:** Streaming SHA-256 calculation for large binaries, CycloneDX SBOM analysis, OSV vulnerability queries with offline fallback, SLSA v1.0 provenance verification, and mandatory blocking policy gates.
3. **AI Engineering:** Explainable composite trust formula ($T = 0.25I + 0.20D + 0.20P + 0.15S + 0.20E$), scikit-learn `IsolationForest` anomaly prioritization model, and deterministic evidence-grounded risk explanations.
4. **Cloud Engineering (AWS):** Amazon DynamoDB single-table design (`BuildTrustRecords`), server-side encrypted Amazon S3 vault, AWS App Runner deployment template (`template.yaml`), CloudWatch structured logging, and least-privilege IAM policies.

---

## 2. System Requirements

- **Python:** Version 3.11 (tested on Python 3.11.9)
- **Node.js:** Version 18+ (tested on Node v22.13.1, npm 10.9.2)
- **Operating System:** Windows (PowerShell) or Linux / macOS

---

## 3. Quick Start Setup (Local Zero-Dependency Mode)

The system works out of the box without requiring AWS credentials by setting `STORAGE_BACKEND=local`.

### 3.1 Clone & Setup Environment
In PowerShell:
```powershell
# 1. Create and activate Python virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install backend dependencies
pip install -r backend\requirements.txt
pip install -r backend\requirements-dev.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..

# 4. Copy environment configuration
Copy-Item .env.example .env
```

### 3.2 Initialize Local Data & Train ML Model
Run the automated bootstrap script to generate sample artifacts, train the local `IsolationForest` model, and seed demonstration release candidates:
```powershell
python infrastructure\scripts\setup_local.py
```

### 3.3 Run Automated Tests
Execute the comprehensive test suite (25 tests covering all domains):
```powershell
$env:PYTHONPATH="D:\BuildTrustAI"
.\.venv\Scripts\pytest backend\tests -v
```

---

## 4. Running the Application

### 4.1 Start the FastAPI Backend
In terminal 1 (with `.venv` activated):
```powershell
$env:PYTHONPATH="D:\BuildTrustAI"
uvicorn backend.app.main:app --reload --port 8000
```
- **Backend API URL:** `http://localhost:8000`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
- **Health Endpoint:** `http://localhost:8000/health`
- **Readiness Endpoint:** `http://localhost:8000/ready`
- **Live Event Stream (SSE):** `http://localhost:8000/api/v1/events`

### 4.2 Start the React Enterprise Dashboard
In terminal 2:
```powershell
cd frontend
npm run dev
```
- **Live React Dashboard:** `http://localhost:5173`

---

## 5. Live Demonstration Scenarios

In the React Dashboard, click **"Demo Scenarios"** in the top navigation bar to trigger real backend workflows:

1. **Scenario A (Trusted Release Pipeline):** Ingests matching SHA-256 digest, clean CycloneDX SBOM, valid SLSA provenance, and passing test results for `rel-payment-1.0.0`. Yields **APPROVE** (Score: 100.0). Emits live SSE events.
2. **Scenario B (Artifact Tampering Detection):** Submits a tampered binary digest for `rel-payment-1.0.0`. Streaming SHA-256 verifier triggers an unconditional **BLOCK** (`TAMPERED_ARTIFACT_DIGEST_MISMATCH`).
3. **Scenario C (Log4Shell CVE Injection):** Injects a critical Log4Shell CVE (CVSS 10.0) into the dependency manifest. OSV engine and zero-tolerance policy trigger an immediate **BLOCK** (`CRITICAL_VULNERABILITY_DETECTED`).
4. **Scenario D (Incomplete Evidence Gate):** Evaluates `rel-analytics-3.0.0` with missing SLSA provenance. Confirms that missing evidence yields **INSUFFICIENT_EVIDENCE** rather than automatic approval.
5. **Scenario E (Mandatory Test Failure):** Submits a test suite with failing security gates for `rel-auth-2.1.0`. Triggers an unconditional **BLOCK** (`SECURITY_GATE_TEST_FAILURE`).

---

## 6. AWS Cloud Deployment

To deploy BuildTrust AI to AWS:

### 6.1 Configure Credentials Safely
Never hardcode AWS keys in code or commit them to git:
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:AWS_REGION="ap-south-1"
```

### 6.2 Execute Cloud Deployment
```powershell
.\infrastructure\scripts\deploy_aws.ps1 -AwsRegion "ap-south-1" -Environment "staging"
```
This script provisions:
- CloudFormation stack (`infrastructure/aws/template.yaml`) with DynamoDB, S3, IAM, and CloudWatch.
- Builds and pushes the Docker container to Amazon ECR.
- Builds the React frontend for CloudFront / S3 hosting.

### 6.3 Connect Backend to AWS
Update `.env`:
```env
APP_ENV=staging
STORAGE_BACKEND=aws
AWS_REGION=ap-south-1
DYNAMODB_TABLE_NAME=BuildTrustRecords-staging
S3_BUCKET_NAME=buildtrust-vault-<account-id>-staging
```

### 6.4 Verification Checks
- Verify DynamoDB: `aws dynamodb scan --table-name BuildTrustRecords-staging --region ap-south-1 --max-items 3`
- Verify S3 Vault: `aws s3 ls s3://buildtrust-vault-<account-id>-staging/`
- Verify Application Readiness: `http://localhost:8000/ready` (reports `"storage_backend": "aws"`)

### 6.5 Resource Cleanup
To remove all AWS resources and prevent unnecessary charges:
```powershell
aws s3 rm s3://buildtrust-vault-<account-id>-staging --recursive --region ap-south-1
aws cloudformation delete-stack --stack-name buildtrust-ai-stack --region ap-south-1
aws ecr delete-repository --repository-name buildtrust-backend --force --region ap-south-1
```

---

## 7. Repository Structure

```
BuildTrustAI/
├── README.md                           # Master documentation & execution instructions
├── .env.example                        # Comprehensive environment template
├── .gitignore                          # Clean exclusions for secrets & local artifacts
├── docker-compose.yml                  # Container orchestration
├── Makefile                            # Standard developer tasks
│
├── docs/                               # Complete project documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── PROBLEM_STATEMENT.md
│   ├── EXISTING_SYSTEMS.md
│   ├── PROPOSED_SYSTEM.md
│   ├── NOVELTY_AND_CONTRIBUTION.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATA_DICTIONARY.md
│   ├── TRUST_SCORE_FORMULA.md
│   ├── SECURITY_POLICIES.md
│   ├── AWS_DEPLOYMENT.md
│   ├── API_DOCUMENTATION.md
│   ├── TESTING_AND_EVALUATION.md
│   ├── DEMONSTRATION_GUIDE.md
│   └── LIMITATIONS_AND_FUTURE_WORK.md
│
├── backend/
│   ├── requirements.txt                # Pinned production dependencies
│   ├── requirements-dev.txt            # Testing dependencies (pytest, moto)
│   ├── pytest.ini                      # Pytest configuration
│   ├── Dockerfile                      # Backend container definition
│   ├── app/
│   │   ├── main.py                     # FastAPI application & lifespan
│   │   ├── config.py                   # Pydantic Settings
│   │   ├── dependencies.py             # Auth & repository dependency injection
│   │   ├── api/                        # REST API routers (auth, projects, releases, evidence, etc.)
│   │   ├── schemas/                    # Pydantic canonical models
│   │   ├── services/                   # Business logic (trust_engine, verifiers, policy_engine)
│   │   ├── repositories/               # Local, DynamoDB, and S3 persistence adapters
│   │   ├── ml/                         # Feature builder, IsolationForest training & inference
│   │   ├── simulator/                  # Automated scenario generators
│   │   └── utils/                      # Hashing, timestamps, path sanitization
│   └── tests/                          # 23 automated tests (data, security, AI, AWS, API)
│
├── frontend/
│   ├── package.json                    # React, Vite, Tailwind, Recharts, Lucide
│   ├── vite.config.ts                  # Vite configuration & proxying
│   ├── Dockerfile                      # Nginx production build
│   └── src/
│       ├── App.tsx                     # Main dashboard coordinator
│       ├── api/client.ts               # Axios API client & scenario triggers
│       ├── hooks/useLiveEvents.ts      # Server-Sent Events hook with fallback polling
│       ├── components/                 # UI components (Navbar, Sidebar, Badges, Modals)
│       ├── pages/                      # 7 dashboard views (Overview, Explorer, Details, etc.)
│       └── types/index.ts              # TypeScript schema interfaces
│
├── infrastructure/
│   ├── aws/                            # SAM CloudFormation template, IAM, S3 policies
│   └── scripts/                        # Setup, seed, test, and AWS deploy scripts
│
└── sample_data/                        # Realistic demo fixtures (manifests, artifacts, SBOMs, scans)
```

---

## 8. License & Academic Submission

Submitted to **Wipro** as a technical mini-project prototype demonstrating multi-domain engineering across Data Engineering, Security Engineering, AI Engineering, and Cloud Engineering (AWS).
