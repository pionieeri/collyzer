import os
import json
import time
from . import log_parser
from . import database

QUEUE_DIR = "queue/pending"
PROCESSED_DIR = "queue/processed"

def process_single_pass(session):
    """
    Processes all files currently in the queue directory in a single pass.
    Returns the number of files processed.
    """
    processed_files = 0
    try:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        filenames = os.listdir(QUEUE_DIR)

        if not filenames:
            print("  Queue is empty.")
            return 0

        for filename in filenames:
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(QUEUE_DIR, filename)
            print(f"  Processing file: {filepath}")

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                host = data.get("host", "unknown-host")
                source_type = data.get("source_type", "unknown-source")
                logs = data.get("logs", [])

                if source_type != "journald":
                    print(f"  Skipping file with unknown source_type: {source_type}")
                    continue

                parsed_entries = []
                for log_entry in logs:
                    parsed = log_parser.parse(log_entry, source_type)
                    if parsed:
                        parsed["host"] = host
                        parsed_entries.append(parsed)
                
                if parsed_entries:
                    database.save_log_entries(session, parsed_entries)
                    print(f"  Saved {len(parsed_entries)} entries to the database.")

                # Move the processed file
                processed_filepath = os.path.join(PROCESSED_DIR, filename)
                os.rename(filepath, processed_filepath)
                print(f"  Moved processed file to {processed_filepath}")
                processed_files += 1

            except json.JSONDecodeError:
                print(f"  Error decoding JSON from {filepath}. Moving to processed.")
                processed_filepath = os.path.join(PROCESSED_DIR, filename)
                os.rename(filepath, processed_filepath)
            except Exception as e:
                print(f"  An error occurred processing {filepath}: {e}")
    
    except FileNotFoundError:
        print(f"  Queue directory not found: {QUEUE_DIR}. Nothing to process.")

    return processed_files

def process_queued_logs(session):
    """
    Scans the queue directory for log files, processes them, and moves them.
    This function runs in a continuous loop.
    """
    print("### Starting Parser Service (Continuous Mode) ###")
    while True:
        try:
            processed_count = process_single_pass(session)
            if processed_count == 0:
                print("  Queue is empty. Waiting for new logs...")
                time.sleep(10)
        except Exception as e:
            print(f"An unexpected error occurred in the parser service: {e}")
            time.sleep(10)
