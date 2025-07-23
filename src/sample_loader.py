import os
from .config import LOG_SOURCES


def load_sample_logs(log_parser) -> list:
    """Reads and parses all available sample log files."""
    all_log_entries = []
    print("### Using Sample Logs ###")
    for source_name in LOG_SOURCES.keys():
        sample_path = os.path.join("sample_logs", f"{source_name}.sample")
        print(f"Reading from: {sample_path}")
        try:
            with open(sample_path, "r") as f:
                log_content = f.read()
                for line in log_content.splitlines():
                    parsed_data = log_parser.parse(line, source_name)
                    if parsed_data:
                        all_log_entries.append(parsed_data)
        except FileNotFoundError:
            print(f"  Error: Sample file not found at {sample_path}")
    return all_log_entries
