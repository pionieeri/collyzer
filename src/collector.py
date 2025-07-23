import os
import paramiko
from concurrent.futures import ThreadPoolExecutor
from .config import HOST_IPS, SSH_USER, SSH_KEY_PATH, LOG_SOURCES

# TODO: handling the same log lines for multiple times -> problem

def _fetch_log_from_client(client: paramiko.SSHClient, host: str, log_path: str) -> str:
    """Fetches a single log file using an existing SSH client connection."""
    print(f"Attempting to fetch {log_path} from {host}...")
    try:
        stdin, stdout, stderr = client.exec_command(f"cat {log_path}")
        log_content = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8").strip()
        if error:
            print(f"  Error on {host} reading {log_path}: {error}")
            return ""
        print(
            f"  Successfully fetched {len(log_content.splitlines())} lines from {log_path} on {host}."
        )
        return log_content
    except Exception as e:
        print(f"  An error occurred while fetching {log_path} from {host}: {e}")
        return ""


def _process_host(host: str, log_parser) -> list:
    """Establishes a single SSH connection to a host and fetches all logs."""
    host_log_entries = []
    client = paramiko.SSHClient()
    client.load_system_host_keys()

    try:
        client.connect(
            hostname=host,
            username=SSH_USER,
            key_filename=os.path.expanduser(SSH_KEY_PATH),
            timeout=10,
        )

        for source_name, remote_path in LOG_SOURCES.items():
            log_content = _fetch_log_from_client(client, host, remote_path)
            if not log_content:
                continue
            for line in log_content.splitlines():
                parsed_data = log_parser.parse(line, source_name)
                if parsed_data:
                    host_log_entries.append(parsed_data)

    except paramiko.AuthenticationException:
        print(
            f"  Authentication failed for {SSH_USER}@{host}. Check your SSH key and username."
        )
    except Exception as e:
        print(f"  An error occurred connecting to {host}: {e}")
    finally:
        if client.get_transport() and client.get_transport().is_active():
            client.close()

    return host_log_entries


def fetch_all_logs_concurrently(log_parser) -> list:
    """
    Fetches logs from all hosts defined in config concurrently.
    Returns a list of all parsed log entries.
    """
    all_log_entries = []
    print("### Fetching Remote Logs ###")
    with ThreadPoolExecutor(max_workers=len(HOST_IPS)) as executor:
        results = executor.map(lambda host: _process_host(host, log_parser), HOST_IPS)
        for host_logs in results:
            all_log_entries.extend(host_logs)
    return all_log_entries
