import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.database import init_db, save_log_entries, LogEntry, _calculate_hash

# Sample log entries for testing
SAMPLE_LOG_1 = {
    'timestamp': datetime(2025, 7, 14, 10, 0, 0),
    'hostname': 'host1',
    'process_name': 'sshd',
    'pid': 1234,
    'message': 'Accepted publickey for user',
    'log_source': 'auth'
}
SAMPLE_LOG_2 = {
    'timestamp': datetime(2025, 7, 14, 10, 0, 5),
    'hostname': 'host1',
    'process_name': 'kernel',
    'pid': None,
    'message': 'Firewall: *TCP_IN Blocked* IN=eth0 ...',
    'log_source': 'syslog'
}
# A duplicate of the first log
SAMPLE_LOG_3 = SAMPLE_LOG_1.copy()


@pytest.fixture
def db_session():
    """Creates a new in-memory SQLite database session for each test."""
    # Using in-memory SQLite for tests is fast and avoids creating files
    session = init_db(':memory:')
    yield session
    session.close()


@patch('src.database.redis_client', new_callable=MagicMock)
def test_save_unique_entries(mock_redis, db_session):
    """Tests that new, unique log entries are saved correctly."""
    entries_to_save = [SAMPLE_LOG_1, SAMPLE_LOG_2]
    hashes = [_calculate_hash(e) for e in entries_to_save]

    # Simulate that Redis has not seen these hashes before
    mock_redis.mget.return_value = [None, None]
    mock_pipeline = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    # Action
    save_log_entries(db_session, entries_to_save)

    # Assertions
    saved_entries = db_session.query(LogEntry).all()
    assert len(saved_entries) == 2
    assert saved_entries[0].hash_id == hashes[0]
    assert saved_entries[1].hash_id == hashes[1]

    # Verify Redis was checked and then updated
    mock_redis.mget.assert_called_once_with(hashes)
    assert mock_pipeline.set.call_count == 2
    mock_pipeline.execute.assert_called_once()


@patch('src.database.redis_client', new_callable=MagicMock)
def test_ignore_duplicate_entries(mock_redis, db_session):
    """Tests that fully duplicate log entries are not saved."""
    entries_to_save = [SAMPLE_LOG_1, SAMPLE_LOG_2]

    # Simulate that Redis has already seen these hashes
    mock_redis.mget.return_value = ['1', '1']
    mock_pipeline = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    # Action
    save_log_entries(db_session, entries_to_save)

    # Assertions
    saved_entries = db_session.query(LogEntry).all()
    assert len(saved_entries) == 0
    mock_pipeline.set.assert_not_called()


@patch('src.database.redis_client', new_callable=MagicMock)
def test_handle_mixed_entries(mock_redis, db_session):
    """Tests saving a mix of new and duplicate entries."""
    # SAMPLE_LOG_3 is a duplicate of SAMPLE_LOG_1
    entries_to_save = [SAMPLE_LOG_1, SAMPLE_LOG_2, SAMPLE_LOG_3]
    
    hash2 = _calculate_hash(SAMPLE_LOG_2)
    # hash3 will be the same as hash1

    # Simulate that Redis has seen hash1 but not hash2
    mock_redis.mget.return_value = ['1', None, '1']
    mock_pipeline = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    # Action
    save_log_entries(db_session, entries_to_save)

    # Assertions
    saved_entries = db_session.query(LogEntry).all()
    assert len(saved_entries) == 1
    assert saved_entries[0].hash_id == hash2

    # Verify Redis was updated with only the new hash
    mock_pipeline.set.assert_called_once_with(hash2, '1')
    mock_pipeline.execute.assert_called_once()
