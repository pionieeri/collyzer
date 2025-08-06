import argparse
import os
import sys
from .database import init_db
from . import collector
from .config import SQLITE_DB_PATH
from .sample_loader import load_sample_logs_to_queue
from . import parser_service

def main():
    parser = argparse.ArgumentParser(description="Log Collector, Parser, and Analyzer")
    parser.add_argument(
        "--use-sample-logs",
        action="store_true",
        help="Use local sample logs instead of fetching from remote hosts."
    )
    args = parser.parse_args()

    # Initialize the database connection
    session, engine = init_db(SQLITE_DB_PATH)

    # Default behavior: run collector, then parser, then analysis.
    print("### Running a single end-to-end cycle ###")

    # 1. Collect logs and write them to the queue
    if args.use_sample_logs:
        print("\n### Using local sample logs. ###")
        load_sample_logs_to_queue()
    else:
        print("\n### Fetching logs from remote hosts. ###")
        collector.fetch_all_logs_concurrently()

    # 2. Process all logs currently in the queue
    print("\n### Starting one-time parsing run ###")
    parser_service.process_single_pass(session)

    # reintroduce later on.
    # 3. Run analysis on the newly added data
    # print("\n### Running Analysis ###")
    # run_analysis(session)

    # reintroduce later on.
    # 4. Create summary views
    # print("\n### Creating Summary Views ###")
    # create_summary_views(engine)

    print("\n### End-to-end cycle finished ###")
    print(f"Database is saved at: {SQLITE_DB_PATH}")
    print(f"To view the logs, run: 'datasette {SQLITE_DB_PATH}'")

    session.close()

if __name__ == "__main__":
    main()
