import os
import paramiko
from concurrent.futures import ThreadPoolExecutor
from .config import HOST_IPS, SSH_USER, SSH_KEY_PATH, LOG_SOURCES
from .log_parser import parse_line


def fetch_logs(host, log_path, ssh_user, ssh_key_path):
    """Fetches a single log file from a remote host."""
    print(f"Attempting to fetch {log_path} from {host}...")
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(hostname=host, username=ssh_user, key_filename=os.path.expanduser(ssh_key_path), timeout=10)
        stdin, stdout, stderr = client.exec_command(f'cat {log_path}')
        log_content = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8').strip()
        if error:
            print(f"  Error on {host} reading {log_path}: {error}")
            return ""
        print(f"  Successfully fetched {len(log_content.splitlines())} lines from {log_path} on {host}.")
        return log_content
    except paramiko.AuthenticationException:
        print(f"  Authentication failed for {ssh_user}@{host}. Check your SSH key and username.")
        return ""
    except Exception as e:
        print(f"  An error occurred connecting to {host}: {e}")
        return ""
    finally:
        if 'client' in locals() and client.get_transport() is not None and client.get_transport().is_active():
            client.close()


def _process_host(host: str) -> list:
    """Helper function to fetch and parse all logs from a single host."""
    host_log_entries = []
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


def fetch_all_logs_concurrently() -> list:
    """
    Fetches logs from all hosts defined in config concurrently.
    Returns a list of all parsed log entries.
    """
    all_log_entries = []
    print("### Fetching Remote Logs ###")
    with ThreadPoolExecutor(max_workers=len(HOST_IPS)) as executor:
        results = executor.map(_process_host, HOST_IPS)
        for host_logs in results:
            all_log_entries.extend(host_logs)
    return all_log_entries
