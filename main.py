import os
import sys
import re
from datetime import datetime

from decouple import config
import paramiko
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# .env
try:
    HOST_IPS = config("HOST_IPS").split(',')
    SSH_USER = config("SSH_USER")
    SSH_KEY_PATH = config("SSH_KEY_PATH")
    SQLITE_DB_PATH = config("SQLITE_DB_PATH")
except Exception as e:
    print(f"Error: Missing configuration in .env file. Please check your settings. Details: {e}")
    sys.exit(1)


# DB Model
Base = sa.orm.declarative_base()

class LogEntry(Base):
    __tablename__ = 'log_entries'
    id = sa.Column(sa.Integer, primary_key=True)
    hostname = sa.Column(sa.String, index=True)
    timestamp = sa.Column(sa.DateTime, index=True)
    process_name = sa.Column(sa.String, index=True)
    pid = sa.Column(sa.Integer, nullable=True)
    message = sa.Column(sa.String)
    log_source = sa.Column(sa.String, index=True)

    def __repr__(self):
        return f"<LogEntry(hostname='{self.hostname}', timestamp='{self.timestamp}', message='{self.message[:30]}...')>"


# Helpers
def fetch_logs(host, log_path, ssh_user, ssh_key_path):
    print(f"Attempting to fetch {log_path} from {host}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Less secure -> replace with host key verification
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

def parse_line(line):
    pattern = re.compile(
        r"^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+([\w\-\.]+)\s+([\w\d\._-]+)(?:\[(\d+)\])?:\s+(.*)$"
    )
    match = pattern.match(line)
    
    if not match:
        return None
    
    timestamp_str = match.group(1)
    current_year = datetime.now().year
    
    full_timestamp_str = f"{current_year} {timestamp_str}"

    try:
        dt_obj = datetime.strptime(full_timestamp_str, "%Y %b %d %H:%M:%S")
        
    except ValueError:
        return None

    pid_str = match.group(4)

    return {
        'timestamp': dt_obj,
        'hostname': match.group(2),
        'process_name': match.group(3),
        'pid': int(pid_str) if pid_str else None,
        'message': match.group(5).strip()
    }

# Main
if __name__ == "__main__":
    print("### Starting Log Collector ###")
    
    engine = sa.create_engine(f'sqlite:///{SQLITE_DB_PATH}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    logs_to_fetch = {
        'syslog': '/var/log/syslog',
        'auth': '/var/log/auth.log'
    }
    
    total_logs_parsed = 0

    for host in HOST_IPS:
        for source_name, remote_path in logs_to_fetch.items():
            log_content = fetch_logs(host, remote_path, SSH_USER, SSH_KEY_PATH)
            
            if not log_content:
                continue

            for line in log_content.splitlines():
                parsed_data = parse_line(line)
                
                if parsed_data:
                    entry = LogEntry(
                        hostname=parsed_data['hostname'],
                        timestamp=parsed_data['timestamp'],
                        process_name=parsed_data['process_name'],
                        pid=parsed_data['pid'],
                        message=parsed_data['message'],
                        log_source=source_name
                    )
                    session.add(entry)
                    total_logs_parsed += 1

    if total_logs_parsed > 0:
        print(f"\nCommitting {total_logs_parsed} new log entries to the database...")
        session.commit()
        print("Commit complete.")
    else:
        print("\nNo new log entries to commit.")

    session.close()
    
    print("\n--- Log Collection Finished ---")
    print(f"Database is saved at: {SQLITE_DB_PATH}")
    print(f"To view the logs, run: 'datasette {SQLITE_DB_PATH}'")
