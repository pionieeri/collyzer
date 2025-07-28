import argparse
import os
import sys
from .database import init_db
from . import collector
from . import parser_service
from .config import SQLITE_DB_PATH
from .analyzer import run_analysis
from .views import create_summary_views

def main():
    parser = argparse.ArgumentParser(description="Log Collector, Parser, and Analyzer")
    parser.add_argument(
        "--service",
        choices=["collector", "parser"],
        help="Run a specific service continuously. 'collector' fetches logs, 'parser' processes them."
    )
    args = parser.parse_args()

    # Initialize the database connection
    session, engine = init_db(SQLITE_DB_PATH)

    if args.service == "collector":
        print("Running the collector service...")
        collector.fetch_all_logs_concurrently()

    elif args.service == "parser":
        print("Running the parser service...")
        parser_service.process_queued_logs(session)

    else:
        # Default behavior: run collector, then parser, then analysis.
        print("### Running a single end-to-end cycle ###")

        # 1. Collect logs and write them to the queue
        collector.fetch_all_logs_concurrently()

        # 2. Process all logs currently in the queue
        print("\n### Starting one-time parsing run ###")
        parser_service.process_single_pass(session)

        # 3. Run analysis on the newly added data
        print("\n### Running Analysis ###")
        run_analysis(session)

        # 4. Create summary views
        print("\n### Creating Summary Views ###")
        create_summary_views(engine)

        print("\n### End-to-end cycle finished ###")
        print(f"Database is saved at: {SQLITE_DB_PATH}")
        print(f"To view the logs, run: 'datasette {SQLITE_DB_PATH}'")

    session.close()

if __name__ == "__main__":
    main()
