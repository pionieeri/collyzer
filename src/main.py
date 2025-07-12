from concurrent.futures import ThreadPoolExecutor
import argparse
import os
# modules
from .config import HOST_IPS, SSH_USER, SSH_KEY_PATH, SQLITE_DB_PATH, LOG_SOURCES
from .collector import fetch_logs
from .log_parser import parse_line
from .database import init_db, save_log_entries

def process_host(host: str) -> list:
    host_log_entries = []
    print("### Fetching Remote Logs ###")
    for source_name, remote_path in LOG_SOURCES.items():
        log_content = fetch_logs(host, remote_path, SSH_USER, SSH_KEY_PATH)
        
        if not log_content:
            continue

        for line in log_content.splitlines():
            parsed_data = parse_line(line)
            
            if parsed_data:
                parsed_data['log_source'] = source_name
                host_log_entries.append(parsed_data)
    
    return host_log_entries

def main():
    parser = argparse.ArgumentParser(description="Log Collector and Analyzer")
    parser.add_argument('--use-sample-logs', action='store_true', help="Use local sample log files instead of fetching from remote hosts.")
    args = parser.parse_args()

    print("### Starting Log Collector ###")
    
    session = init_db(SQLITE_DB_PATH)
    
    all_log_entries = []

    if args.use_sample_logs:
        print("### Using Sample Logs ###")
        for source_name in LOG_SOURCES.keys():
            sample_path = os.path.join('sample_logs', f'{source_name}.sample')
            print(f"Reading from: {sample_path}")
            try:
                with open(sample_path, 'r') as f:
                    log_content = f.read()
                    for line in log_content.splitlines():
                        parsed_data = parse_line(line)
                        if parsed_data:
                            parsed_data['log_source'] = source_name
                            all_log_entries.append(parsed_data)
            except FileNotFoundError:
                print(f"  Error: Sample file not found at {sample_path}")
    else:
        with ThreadPoolExecutor(max_workers=len(HOST_IPS)) as executor:
            # executor.map runs process_host for each item in HOST_IPS concurrently
            # It returns an iterator of the results in the order the tasks were submitted.
            results = executor.map(process_host, HOST_IPS)
            
            for host_logs in results:
                all_log_entries.extend(host_logs)

    save_log_entries(session, all_log_entries)

    session.close()
    
    print("\n### Log Collection Finished ###")
    print(f"Database is saved at: {SQLITE_DB_PATH}")
    print(f"To view the logs, run: 'datasette {SQLITE_DB_PATH}'")

if __name__ == "__main__":
    main()
