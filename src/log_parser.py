import re
from datetime import datetime

# TODO non-parsed lines get discarded -> problem
# TODO stamping current year -> problem
def parse_line(line):
    pattern = re.compile(
        r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+([\w\-\.]+)\s+([\w\d\._-]+)(?:\[(\d+)\])?:\s+(.*)$"
    )
    match = pattern.match(line)

    if not match:
        return None

    timestamp_str = match.group(1)
    current_year = datetime.now().year

    full_timestamp_str = f"{current_year} {timestamp_str}"

    try:
        dt_obj = datetime.strptime(full_timestamp_str, "%Y %b %d %H:%M:%S")

        # Heuristic to fix year-end rollover: if the parsed date is in the
        # future, assume it's from the previous year.
        if dt_obj > datetime.now():
            dt_obj = dt_obj.replace(year=dt_obj.year - 1)

    except ValueError:
        return None

    pid_str = match.group(4)

    return {
        "timestamp": dt_obj,
        "hostname": match.group(2),
        "process_name": match.group(3),
        "pid": int(pid_str) if pid_str else None,
        "message": match.group(5).strip(),
    }
