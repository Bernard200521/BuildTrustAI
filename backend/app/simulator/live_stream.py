import asyncio
import random
import logging
import uuid
from typing import Optional
from backend.app.dependencies import get_repository
from backend.app.schemas.evidence import EvidenceSubmission
from backend.app.services.evidence_service import EvidenceService
from backend.app.services.assessment_service import AssessmentService
from backend.app.services.event_service import broadcaster
from backend.app.utils.timestamps import utc_now_iso

logger = logging.getLogger(__name__)

SAMPLE_PACKAGES = ["urllib3", "cryptography", "requests", "fastapi", "pydantic", "aiohttp", "pyjwt", "certifi"]
SAMPLE_SEVERITIES = ["LOW", "MEDIUM", "HIGH", "LOW", "MEDIUM"]

class LiveTelemetrySimulator:
    """
    Background Real-Time Telemetry Simulator.
    Simulates continuous software supply chain activity (automated test completions,
    dependency checks, OSV CVE disclosures, and live ECTE trust reassessments).
    Emits real-time SSE events so the dashboard actively updates without user interaction.
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._interval_seconds = 6.0
        self._counter = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self, interval_seconds: float = 6.0):
        if self._running:
            return
        self._running = True
        self._interval_seconds = interval_seconds
        self._task = asyncio.create_task(self._loop())
        logger.info("Real-Time Telemetry Simulator started (interval: %ss)", interval_seconds)

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Real-Time Telemetry Simulator stopped.")

    async def generate_single_tick(self):
        """Simulate a single live telemetry event and broadcast it."""
        try:
            repo = get_repository()
            releases = repo.list_releases()
            if not releases:
                return

            # Pick a target release
            target = random.choice(releases)
            self._counter += 1
            now = utc_now_iso()

            event_types = ["TEST_COMPLETED", "DEPENDENCY_VERIFIED", "PROVENANCE_REFRESHED", "SBOM_DELTA"]
            chosen = random.choice(event_types)

            ev_srv = EvidenceService(repo)
            asm_srv = AssessmentService(repo)

            if chosen == "TEST_COMPLETED":
                total = random.randint(40, 150)
                passed = total - random.choice([0, 0, 1])
                failed = total - passed
                ev_srv.ingest_evidence(
                    release_id=target.release_id,
                    submission=EvidenceSubmission(
                        evidence_type="test_results",
                        source="ci-runner-live",
                        payload={
                            "test_framework": "pytest",
                            "total_tests": total,
                            "passed": passed,
                            "failed": failed,
                            "skipped": 0,
                            "mandatory_tests_passed": (failed == 0),
                            "coverage_percentage": round(random.uniform(91.0, 98.5), 1)
                        }
                    ),
                    actor="ci_telemetry_agent"
                )
            elif chosen == "DEPENDENCY_VERIFIED":
                pkg = random.choice(SAMPLE_PACKAGES)
                sev = random.choice(SAMPLE_SEVERITIES)
                ev_srv.ingest_evidence(
                    release_id=target.release_id,
                    submission=EvidenceSubmission(
                        evidence_type="vulnerability_scan",
                        source="osv-continuous-watcher",
                        payload={
                            "scanner_name": "OSV-Continuous-Watcher",
                            "scan_timestamp": now,
                            "total_findings": 1 if sev in ["HIGH", "MEDIUM"] else 0,
                            "critical_count": 0,
                            "high_count": 1 if sev == "HIGH" else 0,
                            "medium_count": 1 if sev == "MEDIUM" else 0,
                            "low_count": 1 if sev == "LOW" else 0,
                            "findings": [
                                {
                                    "id": f"GHSA-live-{random.randint(1000, 9999)}",
                                    "package": pkg,
                                    "version": "1.2.0",
                                    "severity": sev,
                                    "cvss_score": 5.5 if sev == "MEDIUM" else (7.2 if sev == "HIGH" else 3.1),
                                    "summary": f"Automated dependency scan validation for {pkg}",
                                    "advisory_url": "https://osv.dev",
                                    "fixed_version": "1.2.1"
                                }
                            ] if sev in ["HIGH", "MEDIUM"] else []
                        }
                    ),
                    actor="osv_continuous_watcher"
                )

            # Reassess release
            asm = await asm_srv.trigger_reassessment(target.release_id, actor="Telemetry_Simulator")

            # Broadcast live pulse
            await broadcaster.broadcast({
                "type": "LIVE_TELEMETRY_PULSE",
                "event_type": chosen,
                "project_id": target.project_id,
                "release_id": target.release_id,
                "decision": asm.decision,
                "trust_score": asm.trust_score,
                "assessment_version": asm.assessment_version,
                "reason_codes": [f"TELEMETRY_{chosen}"],
                "timestamp": now,
                "tick_count": self._counter
            })
        except Exception as e:
            logger.error("Error in live telemetry simulation: %s", str(e))

    async def _loop(self):
        while self._running:
            try:
                await self.generate_single_tick()
            except Exception as e:
                logger.error("Simulator loop error: %s", str(e))
            await asyncio.sleep(self._interval_seconds)

live_simulator = LiveTelemetrySimulator()
