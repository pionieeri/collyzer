import os
import uuid
import paramiko
from concurrent.futures import ThreadPoolExecutor
from .config import HOST_IPS, SSH_USER, SSH_KEY_PATH
from typing import Optional

QUEUE_DIR = "queue/pending"

def _fetch_journald_logs(client: paramiko.SSHClient, host: str) -> Optional[paramiko.channel.ChannelFile]:
    """Fetches filtered logs from journalctl and returns the stdout stream for processing."""
    command = "journalctl -o json"
    print(f"Attempting to fetch journald logs from {host} with command: '{command}'")
    try:
        stdin, stdout, stderr = client.exec_command(command)
        # Consume stderr to prevent remote process stalls and log non-fatal errors.
        error = stderr.read().decode("utf-8").strip()
        if error:
            print(f"  Stderr from journalctl on {host}: {error}")
        return stdout
    except Exception as e:
        print(f"  An error occurred while fetching logs from {host}: {e}")
        return None

def _process_host(host: str):
    """
    Establishes an SSH connection, fetches journald logs as a raw stream,
    and writes them directly to a file in the queue.
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

        log_stream = _fetch_journald_logs(client, host)
        if not log_stream:
            print(f"  No log stream received from {host}.")
            return

        # Write the raw, line-delimited JSON stream directly to a unique file.
        output_filename = f"{host}_{uuid.uuid4()}.json"
        output_path = os.path.join(QUEUE_DIR, output_filename)

        lines_written = 0
        with open(output_path, "w", encoding="utf-8") as f_out:
            for line in log_stream:
                f_out.write(line)
                lines_written += 1

        if lines_written > 0:
            print(f"  Queued {lines_written} log entries from {host} to {output_path}")
        else:
            # Clean up empty file if no logs were fetched.
            os.remove(output_path)
            print(f"  No new log entries to queue from {host}.")

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
    os.makedirs(QUEUE_DIR, exist_ok=True)

    with ThreadPoolExecutor(max_workers=len(HOST_IPS)) as executor:
        executor.map(_process_host, HOST_IPS)
    print("### Log Collection Finished ###")
