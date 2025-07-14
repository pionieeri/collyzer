import pytest
from unittest.mock import patch, MagicMock
from src.collector import fetch_all_logs_concurrently
import paramiko

# Sample log content to be returned by the mock SSH client
SAMPLE_SYS_LOG = '''Jul 14 10:00:00 host1 kernel: some kernel message
Jul 14 10:00:01 host1 sshd[1234]: another message'''
SAMPLE_AUTH_LOG = '''Jul 14 10:00:02 host1 sshd[1235]: Accepted publickey for user'''


@patch('src.collector.paramiko.SSHClient')
@patch('src.collector.HOST_IPS', ['192.168.1.1'])
def test_fetch_successful(mock_ssh_client):
    """Tests a successful concurrent log fetch from one host."""
    # --- Setup Mock ---
    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance

    # This mock will handle the two calls to exec_command (for syslog and auth.log)
    mock_stdout_sys = MagicMock()
    mock_stdout_sys.read.return_value = SAMPLE_SYS_LOG.encode('utf-8')
    mock_stderr_sys = MagicMock()
    mock_stderr_sys.read.return_value = b''

    mock_stdout_auth = MagicMock()
    mock_stdout_auth.read.return_value = SAMPLE_AUTH_LOG.encode('utf-8')
    mock_stderr_auth = MagicMock()
    mock_stderr_auth.read.return_value = b''

    # The side_effect allows exec_command to return different values each time it's called
    mock_instance.exec_command.side_effect = [
        (None, mock_stdout_sys, mock_stderr_sys),    # First call for syslog
        (None, mock_stdout_auth, mock_stderr_auth), # Second call for auth.log
    ]

    # --- Action ---
    results = fetch_all_logs_concurrently()

    # --- Assertions ---
    # We expect 3 parsed log lines in total from the two sample logs
    assert len(results) == 3
    assert results[0]['message'] == 'some kernel message'
    assert results[1]['process_name'] == 'sshd'
    assert results[2]['log_source'] == 'auth'
    
    # Verify connect was called once for the host
    mock_instance.connect.assert_called_once()
    # Verify exec_command was called twice (once for each log source)
    assert mock_instance.exec_command.call_count == 2


@patch('src.collector.paramiko.SSHClient')
@patch('src.collector.HOST_IPS', ['192.168.1.1'])
def test_fetch_authentication_failure(mock_ssh_client):
    """Tests how the collector handles an SSH authentication failure."""
    # --- Setup Mock ---
    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance
    mock_instance.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    # --- Action ---
    results = fetch_all_logs_concurrently()

    # --- Assertions ---
    # No results should be returned if the connection fails
    assert len(results) == 0
    mock_instance.connect.assert_called_once()
    # exec_command should not be called if connect fails
    mock_instance.exec_command.assert_not_called()


@patch('src.collector.paramiko.SSHClient')
@patch('src.collector.HOST_IPS', ['192.168.1.1'])
def test_fetch_command_error(mock_ssh_client):
    """Tests a successful connection but a failure in the 'cat' command."""
    # --- Setup Mock ---
    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b''
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b'cat: /var/log/syslog: No such file or directory'

    # Both calls to exec_command will return an error
    mock_instance.exec_command.return_value = (None, mock_stdout, mock_stderr)

    # --- Action ---
    results = fetch_all_logs_concurrently()

    # --- Assertions ---
    assert len(results) == 0
    assert mock_instance.exec_command.call_count == 2
