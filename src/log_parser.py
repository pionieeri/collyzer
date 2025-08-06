import re
from datetime import datetime

### Source-specific Payload Parsers ###

def _parse_sshd(message: str, data: dict):
    """Parses sshd log messages for auth events."""
    success_match = re.search(
        r"Accepted \w+ for (?P<user>\S+) from (?P<src_ip>\S+) port (?P<src_port>\d+)", message
    )
    if success_match:
        data.update(success_match.groupdict())
        data["action"] = "allowed"
        data["status"] = "success"
        return

    fail_match = re.search(
        r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<src_ip>\S+) port (?P<src_port>\d+)", message
    )
    if fail_match:
        data.update(fail_match.groupdict())
        data["action"] = "denied"
        data["status"] = "failure"
        return

def _parse_sudo(message: str, data: dict):
    """Parses sudo log messages for command execution."""
    match = re.search(r"^(?P<user>\S+)\s+:.*COMMAND=(?P<command>.*)$", message)
    if match:
        data.update(match.groupdict())
        data["action"] = "allowed"
        data["status"] = "success"

def _parse_kernel_firewall(message: str, data: dict):
    """Parses kernel messages for UFW firewall logs."""
    if "[UFW BLOCK]" not in message:
        return

    fields = {kv.split('=')[0]: kv.split('=')[1] for kv in message.split() if '=' in kv}
    data["action"] = "denied"
    data["status"] = "blocked"
    data["src_ip"] = fields.get("SRC")
    data["dest_ip"] = fields.get("DST")
    data["src_port"] = fields.get("SPT")
    data["dest_port"] = fields.get("DPT")
    data["object"] = fields.get("PROTO") # e.g., 'TCP', 'UDP'

### Utility Functions ###

def _convert_timestamp(ts: str) -> datetime:
    """Converts a UNIX timestamp (with microseconds) from string to datetime."""
    try:
        return datetime.fromtimestamp(int(ts) / 1_000_000)
    except (ValueError, TypeError):
        return datetime.now()

def _get_message(log_entry: dict) -> str:
    """Coerces the MESSAGE field, which can be a list or string, into a single string."""
    msg = log_entry.get("MESSAGE", "")
    if isinstance(msg, list):
        return "\n".join(map(str, msg))
    return str(msg)

### Main Parser Function ###

def parse(log_entry: dict):
    """
    Parses a journald entry by mapping base fields and then
    dispatching to source-specific payload parsers.
    """

    message_str = _get_message(log_entry)

    # Refined log source determination
    log_source = log_entry.get("SYSLOG_IDENTIFIER")
    if not log_source:
        unit = log_entry.get("_SYSTEMD_UNIT", "")
        comm = log_entry.get("_COMM", "")
        log_source = unit.replace(".service", "") if unit else comm

    cim_mapping = {
        "timestamp": _convert_timestamp(log_entry.get("__REALTIME_TIMESTAMP")),
        "hostname": log_entry.get("_HOSTNAME", "unknown-host"), # Sourced from the log entry itself
        "log_source": log_source,
        "process_name": log_source, # Made consistent with log_source
        "pid": log_entry.get("_PID"),
        "uid": log_entry.get("_UID"),
        "gid": log_entry.get("_GID"),
        "message": message_str,
        "action": "observed",
        "status": None,
        "user": None,
        "src_ip": None,
        "dest_ip": None,
        "src_port": None,
        "dest_port": None,
        "command": None,
        "object": None,
    }

    # Stage Two: Dispatch to source-specific payload parser
    if cim_mapping['log_source'] == 'sshd':
        _parse_sshd(cim_mapping['message'], cim_mapping)
    elif cim_mapping['log_source'] == 'sudo':
        _parse_sudo(cim_mapping['message'], cim_mapping)
    elif cim_mapping['log_source'] == 'kernel':
        _parse_kernel_firewall(cim_mapping['message'], cim_mapping)

    # Sanitize port fields to ensure they are integers or None
    for port_field in ['src_port', 'dest_port']:
        if cim_mapping[port_field]:
            try:
                cim_mapping[port_field] = int(cim_mapping[port_field])
            except (ValueError, TypeError):
                cim_mapping[port_field] = None

    return cim_mapping
