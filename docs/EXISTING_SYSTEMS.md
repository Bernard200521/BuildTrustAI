# Existing Systems & Comparative Analysis

To contextualize BuildTrust AI and evaluate the state of the art, we review established open standards, security frameworks, and scanners currently employed across software supply chains.

---

## 1. Industry Frameworks and Tools

### 1.1 NIST Secure Software Development Framework (SSDF — SP 800-218)
- **Official Documentation:** [NIST SP 800-218](https://csrc.nist.gov/publications/detail/sp/800-218/final)
- **Scope & Capabilities:** Defines best practices across the software development life cycle (SDLC). Emphasizes protecting software from tampering, producing well-secured software, and responding rapidly to disclosed vulnerabilities.
- **Limitation:** NIST SSDF provides high-level organizational requirements and practice definitions; it does not provide an automated runtime engine to calculate composite release trust scores.

### 1.2 SLSA (Supply-chain Levels for Software Artifacts)
- **Official Documentation:** [SLSA Specification v1.0](https://slsa.dev/spec/v1.0/)
- **Scope & Capabilities:** Provides a security framework and verifiable specification for build provenance and supply chain integrity. Establishes Level 1 through Level 3 build assurance by verifying immutable builder identities, isolated build environments, and cryptographically signed in-toto attestations.
- **Limitation:** SLSA focuses on *how* an artifact was produced (provenance), not whether the artifact contains known vulnerabilities or satisfies functional regression tests.

### 1.3 OWASP Dependency-Check
- **Official Documentation:** [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- **Scope & Capabilities:** A Software Composition Analysis (SCA) tool that detects publicly disclosed vulnerabilities contained within project dependencies against the National Vulnerability Database (NVD).
- **Limitation:** Primarily runs as a point-in-time build plugin. Does not continuously reassess staged releases as fresh evidence arrives post-build, nor does it evaluate build provenance or artifact tampering.

### 1.4 CycloneDX (OWASP Software Bill of Materials Standard)
- **Official Documentation:** [CycloneDX Specification](https://cyclonedx.org/)
- **Scope & Capabilities:** An enterprise lightweight SBOM standard designed for application security contexts and supply chain component analysis. Provides structured schemas for components, licenses, and external references.
- **Limitation:** CycloneDX is an evidence data format. It does not enforce admission policies or compute adaptive release gate decisions.

### 1.5 OSV.dev (Open Source Vulnerabilities)
- **Official Documentation:** [OSV.dev API](https://osv.dev/docs/)
- **Scope & Capabilities:** A distributed, open-source vulnerability database aggregating advisories across PyPI, Maven, Go, npm, and Linux ecosystems with precise commit-level and version-range matching.
- **Limitation:** Provides raw vulnerability advisories via REST API; it does not correlate advisory findings with artifact integrity or release gates.

---

## 2. Comparative Matrix

| Capability | NIST SSDF | SLSA v1.0 | OWASP Dep-Check | CycloneDX | BuildTrust AI (ECTE) |
|---|---|---|---|---|---|
| **Cryptographic Digest Verification** | Policy Req | Yes (Digest in Provenance) | No | Optional Hashes | **Implemented Streaming SHA-256** |
| **SCA Vulnerability Lookup** | Policy Req | No | Yes (Point-in-time) | No (Format only) | **Continuous OSV Integration** |
| **Build Provenance Verification** | Policy Req | Yes | No | Metadata Only | **SLSA v1.0 + Cosign Verification** |
| **Continuous Reassessment on Evidence Shift** | Conceptual | No | No | No | **Implemented (ECTE)** |
| **AI Anomaly Prioritization** | No | No | No | No | **Implemented (IsolationForest)** |
| **Deterministic Release Gates** | Guidelines | Policy Enforced | Build Fail Option | Format Only | **Implemented (APPROVE/REVIEW/BLOCK)** |
| **Live Web Security Dashboard** | None | None | HTML Report | None | **Live React Enterprise Dashboard (SSE)** |
