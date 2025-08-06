import os
import json
import time
from . import log_parser
from . import database

QUEUE_DIR = "queue/pending"
PROCESSED_DIR = "queue/processed"
BATCH_SIZE = 500  # Number of log entries to save to DB at a time

def process_single_pass(session):
    """
    Processes all files in the queue, combining memory-efficient batching
    with atomic, file-level database transactions.
    """
    processed_files_count = 0
    try:
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        filenames = os.listdir(QUEUE_DIR)

        if not filenames:
            print("  Queue is empty.")
            return 0

    except FileNotFoundError:
        print(f"  Queue directory not found: {QUEUE_DIR}. Nothing to process.")
        return 0

    for filename in filenames:
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(QUEUE_DIR, filename)
        processed_filepath = os.path.join(PROCESSED_DIR, filename)
        print(f"  Processing file: {filename}")

        try:
            batch = []
            total_entries_in_file = 0

            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_entry = json.loads(line)
                        parsed = log_parser.parse(log_entry)
                        if parsed:
                            batch.append(parsed)

                        if len(batch) >= BATCH_SIZE:
                            database.save_log_entries(session, batch)
                            total_entries_in_file += len(batch)
                            batch = [] # Clear the batch for the next set

                    except json.JSONDecodeError:
                        print(f"    Warning: Skipping malformed JSON line in {filename}: {line[:100]}")

            # Save the final, smaller batch if any entries remain
            if batch:
                database.save_log_entries(session, batch)
                total_entries_in_file += len(batch)

            # Commit only after the entire file is successfully read.
            if total_entries_in_file > 0:
                session.commit()
                print(f"  Successfully committed {total_entries_in_file} entries to the database.")
            else:
                print("  No valid entries found to commit.")

            processed_files_count += 1

        except Exception as e:
            # If anything fails (DB error, file read error), roll back the entire transaction for this file.
            print(f"  An error occurred processing {filepath}: {e}")
            print("  Rolling back transaction for this file.")
            session.rollback()

        finally:
            # Always move the file to prevent it from being re-processed,
            # regardless of whether it succeeded or failed (poisonous message handling).
            os.rename(filepath, processed_filepath)
            print(f"  Moved file to {processed_filepath}")

    return processed_files_count
