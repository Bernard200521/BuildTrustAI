from typing import Dict, Any, List

class TestResultAnalyzer:
    """
    Analyzes test suite execution reports and security regression suites.
    Calculates Test & Security Check score (S).
    """

    @staticmethod
    def analyze_results(payload: Dict[str, Any]) -> Dict[str, Any]:
        total = payload.get("total_tests", 0)
        passed = payload.get("passed", 0)
        failed = payload.get("failed", 0)
        skipped = payload.get("skipped", 0)
        mandatory_passed = payload.get("mandatory_tests_passed", True)
        suites: List[Dict[str, Any]] = payload.get("suites", [])

        # Check if any mandatory suite failed
        for s in suites:
            if s.get("mandatory", True) and not s.get("passed", False):
                mandatory_passed = False

        if not mandatory_passed:
            score = 0.0
            status = "FAILED"
            details = "One or more mandatory security/functional test suites failed."
        elif total == 0:
            score = 0.0
            status = "FAILED"
            details = "No tests were executed."
        else:
            pass_rate = (passed / total) * 100.0 if total > 0 else 0.0
            # Non-mandatory test failures penalize pass rate proportionally
            score = round(pass_rate, 1)
            status = "VERIFIED" if failed == 0 else "PARTIAL"
            details = f"{passed}/{total} tests passed ({skipped} skipped, {failed} failed)."

        return {
            "score": score,
            "status": status,
            "mandatory_passed": mandatory_passed,
            "details": details,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }
