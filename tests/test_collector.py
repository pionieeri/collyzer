
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
    # --- Setup Mocks ---
    mock_parser = MagicMock()
    mock_parser.parse.side_effect = lambda line, source: {'raw_message': line, 'log_source': source} # Simple mock parser

    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance

    mock_stdout_sys = MagicMock()
    mock_stdout_sys.read.return_value = SAMPLE_SYS_LOG.encode('utf-8')
    mock_stderr_sys = MagicMock()
    mock_stderr_sys.read.return_value = b''

    mock_stdout_auth = MagicMock()
    mock_stdout_auth.read.return_value = SAMPLE_AUTH_LOG.encode('utf-8')
    mock_stderr_auth = MagicMock()
    mock_stderr_auth.read.return_value = b''

    mock_instance.exec_command.side_effect = [
        (None, mock_stdout_sys, mock_stderr_sys),
        (None, mock_stdout_auth, mock_stderr_auth),
    ]

    # --- Action ---
    results = fetch_all_logs_concurrently(mock_parser)

    # --- Assertions ---
    assert len(results) == 3 # 2 from syslog, 1 from auth.log
    assert results[0]['log_source'] == 'syslog'
    assert results[2]['log_source'] == 'auth'
    assert 'some kernel message' in results[0]['raw_message']
    
    mock_instance.connect.assert_called_once()
    assert mock_instance.exec_command.call_count == 2
    assert mock_parser.parse.call_count == 3


@patch('src.collector.paramiko.SSHClient')
@patch('src.collector.HOST_IPS', ['192.168.1.1'])
def test_fetch_authentication_failure(mock_ssh_client):
    """Tests how the collector handles an SSH authentication failure."""
    # --- Setup Mocks ---
    mock_parser = MagicMock()
    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance
    mock_instance.connect.side_effect = paramiko.AuthenticationException("Auth failed")

    # --- Action ---
    results = fetch_all_logs_concurrently(mock_parser)

    # --- Assertions ---
    assert len(results) == 0
    mock_instance.connect.assert_called_once()
    mock_instance.exec_command.assert_not_called()


@patch('src.collector.paramiko.SSHClient')
@patch('src.collector.HOST_IPS', ['192.168.1.1'])
def test_fetch_command_error(mock_ssh_client):
    """Tests a successful connection but a failure in the 'cat' command."""
    # --- Setup Mocks ---
    mock_parser = MagicMock()
    mock_instance = MagicMock()
    mock_ssh_client.return_value = mock_instance

    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b''
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b'cat: /var/log/syslog: No such file or directory'

    mock_instance.exec_command.return_value = (None, mock_stdout, mock_stderr)

    # --- Action ---
    results = fetch_all_logs_concurrently(mock_parser)

    # --- Assertions ---
    assert len(results) == 0
    assert mock_instance.exec_command.call_count == 2
