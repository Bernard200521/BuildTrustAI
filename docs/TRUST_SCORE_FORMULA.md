# Trust Score Formula & Mathematical Formulation — BuildTrust AI

## 1. Baseline Composite Formula

The initial transparent baseline implemented by the Evidence-Change Trust Engine (ECTE) computes release trustworthiness as a weighted sum of five normalized security components:

$$T = 0.25 \cdot I + 0.20 \cdot D + 0.20 \cdot P + 0.15 \cdot S + 0.20 \cdot E$$

Where:
- $0.0 \le T \le 100.0$
- $I$: Artifact Integrity Score ($w_I = 0.25$)
- $D$: Dependency Security Score ($w_D = 0.20$)
- $P$: Provenance Verification Score ($w_P = 0.20$)
- $S$: Test & Security Regression Score ($w_S = 0.15$)
- $E$: Evidence Completeness Score ($w_E = 0.20$)

---

## 2. Component Formulations

### 2.1 Artifact Integrity Score ($I$)
Evaluates cryptographic digest match between calculated streaming SHA-256 and expected manifest digest:
$$I = \begin{cases} 
100.0 & \text{if calculated SHA-256 matches expected digest} \\
0.0 & \text{if SHA-256 digest mismatch is detected} \\
\text{null} & \text{if binary artifact or expected digest is unavailable}
\end{cases}$$
> **Safety Principle:** A confirmed mismatch ($I = 0.0$) independently triggers an unconditional policy gate `BLOCK`, regardless of the composite score $T$.

### 2.2 Dependency Security Score ($D$)
Uses normalized, deduplicated CVE/GHSA findings from OSV.dev and CycloneDX SBOM:
$$D = \max(0.0, 100.0 - (40 \cdot C + 20 \cdot H + 8 \cdot M + 2 \cdot L))$$
Where:
- $C$: Verified Critical severity findings (CVSS $\ge 9.0$)
- $H$: Verified High severity findings ($7.0 \le \text{CVSS} \le 8.9$)
- $M$: Verified Medium severity findings ($4.0 \le \text{CVSS} \le 6.9$)
- $L$: Verified Low severity findings ($0.1 \le \text{CVSS} \le 3.9$)

*Assumption Note:* These weights represent prototype baseline assumptions designed to penalize severe supply-chain risks heavily while permitting minor advisories under warning thresholds.

### 2.3 Provenance Verification Score ($P$)
Validates SLSA build level, builder identity, source commit, and cryptographic Cosign signatures:
$$P = \begin{cases}
100.0 & \text{if mandatory checks pass and attestation has verified Cosign signature} \\
85.0 & \text{if mandatory checks pass but optional Cosign signature is not performed} \\
0.0 & \text{if mandatory builder identity or git commit mismatch fails} \\
\text{null} & \text{if provenance attestation is missing}
\end{cases}$$

### 2.4 Test Results Score ($S$)
Evaluates automated test suite executions:
$$S = \begin{cases}
0.0 & \text{if any mandatory security/regression test fails} \\
\left(\frac{\text{Passed Tests}}{\text{Total Tests}}\right) \times 100.0 & \text{if all mandatory tests pass} \\
\text{null} & \text{if test results are missing}
\end{cases}$$

### 2.5 Evidence Completeness Score ($E$)
Ensures that releases cannot pass gates simply by withholding negative evidence:
$$E = 100.0 \times \frac{\text{Valid Required Evidence Envelopes}}{\text{Total Configured Required Evidence Envelopes}}$$

---

## 3. Handling Missing Evidence (Incomplete Records)

A critical principle of ECTE is that **missing evidence is never equated with zero vulnerabilities or passing checks**.
- If required evidence items are missing, the assessment is classified as `INSUFFICIENT_EVIDENCE`.
- Missing values are never silently replaced with 100.0.
- The system reports `INSUFFICIENT_EVIDENCE` until all mandatory envelope requirements are satisfied.
