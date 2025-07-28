import json
from datetime import datetime

# This is a simplified parser specifically for journald JSON output.
# The complex, rule-based engine is no longer needed for this source.

def _convert_timestamp(ts: str) -> datetime:
    """Converts a UNIX timestamp (with microseconds) from string to datetime."""
    try:
        # journalctl timestamps are in microseconds since the epoch
        return datetime.fromtimestamp(int(ts) / 1_000_000)
    except (ValueError, TypeError):
        # Fallback for invalid or missing timestamps
        return datetime.now()

def parse(log_entry: dict, source_type: str):
    """
    Parses a single JSON log entry from journald.
    The `log_entry` is already a dictionary because it was parsed from JSON in the collector.
    `source_type` is kept for consistency but is expected to be 'journald'.
    """
    if source_type != "journald" or not isinstance(log_entry, dict):
        return None

    # Map the journald fields to our Common Information Model (CIM).
    # This mapping is now done directly in the code.
    cim_mapping = {
        "timestamp": _convert_timestamp(log_entry.get("__REALTIME_TIMESTAMP")),
        "hostname": log_entry.get("_HOSTNAME", "unknown"),
        "process_name": log_entry.get("_SYSTEMD_UNIT", log_entry.get("_COMM")),
        "pid": log_entry.get("_PID"),
        "uid": log_entry.get("_UID"),
        "gid": log_entry.get("_GID"),
        "message": log_entry.get("MESSAGE", ""),
        "raw_message": json.dumps(log_entry), # Store the original JSON object
        "log_source": source_type,
        # Default action, can be overridden by analysis rules later
        "action": "observed",
    }

    return cim_mapping
