from datetime import datetime, timezone

def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()

def parse_iso(ts_str: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a datetime object."""
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
