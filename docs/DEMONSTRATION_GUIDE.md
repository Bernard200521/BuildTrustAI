# Demonstration Guide & Evaluation Scenarios — BuildTrust AI

Follow these step-by-step instructions to demonstrate the Evidence-Change Trust Engine (ECTE) and live React dashboard.

---

## 1. Quick Start Demonstration

### Step 1: Start the Backend
Open a terminal in `d:\BuildTrustAI`:
```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
uvicorn backend.app.main:app --reload --port 8000
```
*Backend runs at:* `http://localhost:8000`  
*Swagger Documentation:* `http://localhost:8000/docs`

### Step 2: Start the React Dashboard
Open a second terminal in `d:\BuildTrustAI\frontend`:
```powershell
npm run dev
```
*React Dashboard runs at:* `http://localhost:5173`

---

## 2. Interactive Demonstration Scenarios

In the React Dashboard, click the **"Demo Scenarios"** button in the top navigation bar to open the live scenario trigger modal.

### Scenario A: Trusted Release Candidate
- **Context:** Software build candidate `rel-payment-1.0.0` has verified streaming SHA-256 integrity, a clean CycloneDX SBOM, valid SLSA provenance, and all security tests passed.
- **Action:** Click **"Run Scenario A"** in the modal.
- **Observed Behavior:**
  - Trust score recomputes to **100.0**.
  - Final decision updates to **APPROVE** (green badge).
  - Component breakdown displays $I=100, D=100, P=100, S=100, E=100$.
  - Live Event Monitor logs an `ASSESSMENT_CHANGED` transition.

### Scenario B: Dynamic Vulnerability Injection (Live Shift)
- **Context:** A newly disclosed critical remote code execution vulnerability (Log4Shell) is submitted for the staged candidate.
- **Action:** Click **"Run Scenario B"** in the modal.
- **Observed Behavior:**
  - ECTE detects the evidence change without manual refresh.
  - Dependency score $D$ drops from 100 to 60.
  - Policy engine detects $\ge 1$ critical CVE under zero-tolerance policy.
  - Final decision immediately flips from **APPROVE $\rightarrow$ BLOCK** (red badge).
  - Blocking reason explains: *"Release contains 1 verified CRITICAL vulnerability finding(s)."*
  - The live dashboard updates automatically via Server-Sent Events (SSE).

### Scenario C: Artifact Tampering Detection
- **Context:** A release candidate has an altered binary payload (simulated malicious supply-chain swap).
- **Action:** Click **"Run Scenario C"** in the modal.
- **Observed Behavior:**
  - Artifact verifier reports calculated SHA-256 differs from trusted reference ($I = 0.0$).
  - Policy engine unconditionally enforces **BLOCK**.
  - Demonstrates that even if other components pass, mandatory integrity violations cannot be overridden.

### Scenario D: Missing Provenance / Incomplete Evidence
- **Context:** Inspect candidate `rel-analytics-3.0.0` in the Release Explorer.
- **Observed Behavior:**
  - SBOM and SLSA Provenance have not been submitted.
  - Decision state displays **INSUFFICIENT_EVIDENCE** (indigo badge).
  - Demonstrates that missing evidence is never silently treated as 100.

### Scenario E: AI Anomaly Prioritization
- **Context:** Inspect candidate `rel-worker-1.5.0` in the AI Explanation Panel.
- **Observed Behavior:**
  - Features an unusual concentration of medium/high findings combined with non-standard builder identity.
  - IsolationForest model flags the candidate as an outlier.
  - Score change explanations highlight the multidimensional risk profile.

### Scenario F: Real-Time SSE Stream Verification
- **Context:** Open the **"Live Event Monitor"** tab.
- **Observed Behavior:**
  - Shows green blinking `LIVE SSE STREAM ACTIVE` indicator.
  - Trigger any scenario in another tab or via cURL.
  - Events stream into the feed instantly with timestamps, delta version numbers, and reason codes without refreshing the browser.
