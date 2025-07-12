import paramiko
import os

def fetch_logs(host, log_path, ssh_user, ssh_key_path):
    print(f"Attempting to fetch {log_path} from {host}...")
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.connect(hostname=host, username=ssh_user, key_filename=os.path.expanduser(ssh_key_path), timeout=10)
        stdin, stdout, stderr = client.exec_command(f'cat {log_path}')

        # Read the log content from stdout
        log_content = stdout.read().decode('utf-8')
        # Check for errors from the command execution itself
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
