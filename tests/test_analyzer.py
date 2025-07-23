from unittest.mock import patch, mock_open
import pytest
from src.analyzer import run_analysis
from src.database import LogEntry
from datetime import datetime

# Sample CIM-compliant log entries for testing
ANALYZER_LOGS = [
    LogEntry(
        timestamp=datetime(2025, 7, 16, 10, 0, 0),
        hostname='host1',
        log_source='auth',
        action='failure',
        app='sshd',
        category='authentication',
        user='invalid_user'
    ),
    LogEntry(
        timestamp=datetime(2025, 7, 16, 10, 5, 0),
        hostname='host2',
        log_source='auth',
        action='success',
        app='sudo',
        category='privilege-escalation',
        user='admin'
    ),
    LogEntry(
        timestamp=datetime(2025, 7, 16, 10, 10, 0),
        hostname='host1',
        log_source='auth',
        action='success',
        app='sshd',
        category='authentication',
        user='testuser'
    )
]

# Sample YAML content for the new analysis rules file
SAMPLE_ANALYSIS_RULES_YAML = """
- name: "SSH Authentication Failure"
  query_filters:
    action: "failure"
    category: "authentication"
    app: "sshd"

- name: "Successful Sudo Command"
  query_filters:
    action: "success"
    app: "sudo"
"""

@pytest.fixture
def mock_analysis_rules_file(monkeypatch):
    """Mocks the open() call to provide the test analysis rules."""
    mock_file = mock_open(read_data=SAMPLE_ANALYSIS_RULES_YAML)
    monkeypatch.setattr("builtins.open", mock_file)

def test_run_analysis_with_findings(db_session, capsys, mock_analysis_rules_file):
    """Tests that the analyzer correctly finds and reports alerts using query_filters."""
    db_session.add_all(ANALYZER_LOGS)
    db_session.commit()

    run_analysis(db_session)

    captured = capsys.readouterr()

    # Assert that alerts for both rules were printed
    assert "ALERT [SSH Authentication Failure]: Found 1 matching log entries!" in captured.out
    assert "ALERT [Successful Sudo Command]: Found 1 matching log entries!" in captured.out
    # Check for specific details in the output
    assert "User: invalid_user" in captured.out
    assert "User: admin" in captured.out

def test_run_analysis_no_findings(db_session, capsys, mock_analysis_rules_file):
    """Tests that no alerts are generated when no logs match the filters."""
    # The database is empty, so no findings are expected
    run_analysis(db_session)
    captured = capsys.readouterr()
    assert "ALERT" not in captured.out