from unittest.mock import patch, MagicMock
from datetime import datetime

from src.database import save_log_entries, LogEntry

SAMPLE_LOG_1 = {
    'timestamp': datetime(2025, 7, 14, 10, 0, 0),
    'hostname': 'host1',
    'action': 'success',
    'process_name': 'sshd',
    'pid': '1234',
    'uid': '1000',
    'gid': '1000',
    'message': 'Accepted publickey for user testuser'
}

SAMPLE_LOG_2 = {
    'timestamp': datetime(2025, 7, 14, 10, 0, 5),
    'hostname': 'host1',
    'action': 'blocked',
    'process_name': 'firewall',
    'pid': '0',
    'uid': '0',
    'gid': '0',
    'message': 'Firewall: *TCP_IN Blocked* IN=eth0 ...'
}

def test_save_log_entries(db_session):
    """Tests that log entries are saved correctly."""
    entries_to_save = [SAMPLE_LOG_1, SAMPLE_LOG_2]

    # Action
    save_log_entries(db_session, entries_to_save)

    # Assertions
    saved_entries = db_session.query(LogEntry).all()
    assert len(saved_entries) == 2
    assert saved_entries[0].hostname == 'host1'
    assert saved_entries[1].process_name == 'firewall'
