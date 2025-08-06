import os
import uuid
import json

def load_sample_logs_to_queue():
    """
    Reads sample log files, injects hostname metadata, and writes them to the
    queue as line-delimited JSON streams, matching the remote collector format.
    """
    pending_dir = os.path.join("queue", "pending")
    os.makedirs(pending_dir, exist_ok=True)

    sample_dir = "sample_logs"
    try:
        sample_files = os.listdir(sample_dir)
    except FileNotFoundError:
        print(f"  Error: Sample log directory not found at '{sample_dir}'. No samples loaded.")
        return

    for sample_file in sample_files:
        if not sample_file.endswith(".json"):
            continue

        source_name = os.path.splitext(sample_file)[0]
        sample_path = os.path.join(sample_dir, sample_file)
        queue_file_path = os.path.join(
            pending_dir, f"sample-{source_name}_{uuid.uuid4()}.json"
        )

        lines_written = 0
        try:
            with open(sample_path, "r", encoding="utf-8") as f_in, \
                 open(queue_file_path, "w", encoding="utf-8") as f_out:

                for line in f_in:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        # The critical step: load, modify, and dump
                        log_entry = json.loads(line)
                        log_entry["_HOSTNAME"] = f"sample-{source_name}"
                        f_out.write(json.dumps(log_entry) + "\n")
                        lines_written += 1
                    except json.JSONDecodeError:
                        print(f"  Warning: Skipping malformed JSON line in {sample_path}: {line[:100]}")

            if lines_written > 0:
                print(f"  Copied and structured {lines_written} entries from {sample_path} to {queue_file_path}")
            else:
                os.remove(queue_file_path)
                print(f"  No valid log entries in {sample_path}; empty queue file removed.")

        except FileNotFoundError:
            print(f"  Error: Sample file not found at {sample_path} during processing.")
        except Exception as e:
            print(f"  An unexpected error occurred processing {sample_path}: {e}")
