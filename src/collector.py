import os
import uuid
import json
import paramiko
from concurrent.futures import ThreadPoolExecutor
from .config import HOST_IPS, SSH_USER, SSH_KEY_PATH

# The collector's responsibility is now to fetch raw logs and queue them.
# The parsing is handled by a separate service.

QUEUE_DIR = "queue/pending"


def _fetch_journald_logs(client: paramiko.SSHClient, host: str) -> str:
    """Fetches logs from journalctl on a remote host as a JSON stream."""
    command = "journalctl -o json"
    print(f"Attempting to fetch journald logs from {host}...")
    try:
        stdin, stdout, stderr = client.exec_command(command)
        log_content = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8").strip()
        if error:
            # journalctl often prints non-fatal errors to stderr, so we log them but don't fail.
            print(f"  Stderr from journalctl on {host}: {error}")
        if not log_content:
            print(f"  No log content received from {host}.")
            return ""
        print(f"  Successfully fetched {len(log_content.splitlines())} lines from {host}.")
        return log_content
    except Exception as e:
        print(f"  An error occurred while fetching logs from {host}: {e}")
        return ""


def _process_host(host: str):
    """
    Establishes an SSH connection to a host, fetches journald logs,
    and writes them to a file in the queue.
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()

    try:
        client.connect(
            hostname=host,
            username=SSH_USER,
            key_filename=os.path.expanduser(SSH_KEY_PATH),
            timeout=10,
        )

        log_content = _fetch_journald_logs(client, host)
        if not log_content:
            return

        # Each line from journalctl is a separate JSON object.
        # We'll process them into a list.
        log_lines = log_content.strip().splitlines()
        
        # We can't assume that every line is a valid JSON object, so we'll try to parse them one by one
        json_payload = []
        for line in log_lines:
            try:
                json_payload.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  Warning: Could not decode JSON from line on {host}: {line}")
                continue

        # Write the payload to a unique file in the queue.
        output_filename = f"{uuid.uuid4()}.json"
        output_path = os.path.join(QUEUE_DIR, output_filename)

        with open(output_path, "w") as f:
            json.dump({"host": host, "source_type": "journald", "logs": json_payload}, f)

        print(f"  Queued logs from {host} to {output_path}")

    except paramiko.AuthenticationException:
        print(
            f"  Authentication failed for {SSH_USER}@{host}. Check your SSH key and username."
        )
    except Exception as e:
        print(f"  An error occurred connecting to {host}: {e}")
    finally:
        if client.get_transport() and client.get_transport().is_active():
            client.close()


def fetch_all_logs_concurrently():
    """
    Fetches logs from all hosts defined in config concurrently and queues them.
    """
    print("### Fetching Remote Logs ###")
    # Ensure the queue directory exists
    os.makedirs(QUEUE_DIR, exist_ok=True)

    with ThreadPoolExecutor(max_workers=len(HOST_IPS)) as executor:
        # No parser is passed anymore
        executor.map(_process_host, HOST_IPS)
    print("### Log Collection Finished ###")
