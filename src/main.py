import argparse
import os
import sys
from .database import init_db, save_log_entries
from .collector import fetch_all_logs_concurrently
from .sample_loader import load_sample_logs
from .config import SQLITE_DB_PATH
from .analyzer import run_analysis
from .views import create_summary_views


def main():
    lock_file = "collyzer.lock"
    if os.path.exists(lock_file):
        print("Lock file exists, another instance of the script is running. Exiting.")
        sys.exit()
    open(lock_file, "w").close() 
    parser = argparse.ArgumentParser(description="Log Collector and Analyzer")
    parser.add_argument(
        "--use-sample-logs",
        action="store_true",
        help="Use local sample log files instead of fetching from remote hosts.",
    )
    args = parser.parse_args()

    print("### Starting Log Collector ###")

    session, engine = init_db(SQLITE_DB_PATH)

    if args.use_sample_logs:
        all_log_entries = load_sample_logs()
    else:
        all_log_entries = fetch_all_logs_concurrently()

    save_log_entries(session, all_log_entries)

    run_analysis(session)

    create_summary_views(engine)

    session.close()

    print("\n### Log Collection Finished ###")
    print(f"Database is saved at: {SQLITE_DB_PATH}")
    print(f"To view the logs, run: 'datasette {SQLITE_DB_PATH}'")
    try:
        os.remove(lock_file)
    except Exception as e:
        pass


if __name__ == "__main__":
    main()
