from unittest.mock import patch, MagicMock
import paramiko
from src.collector import fetch_all_logs_concurrently, _process_host


@patch('src.collector._process_host')
@patch('src.collector.HOST_IPS', ['192.168.1.1', '192.168.1.2'])
def test_fetch_all_logs_concurrently(mock_process_host):
    """Tests that fetch_all_logs_concurrently calls _process_host for each host."""
    fetch_all_logs_concurrently()
    assert mock_process_host.call_count == 2
    mock_process_host.assert_any_call('192.168.1.1')
    mock_process_host.assert_any_call('192.168.1.2')