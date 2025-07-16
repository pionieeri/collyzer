from unittest.mock import patch, mock_open
from src.analyzer import run_analysis
from src.database import LogEntry
from datetime import datetime

# Sample log entries for testing the analyzer
ANALYZER_LOGS = [
    LogEntry(
        timestamp=datetime(2025, 7, 15, 10, 0, 0),
        hostname='host1',
        log_source='auth',
        message='Failed password for invalid user admin from 1.2.3.4 port 1234 ssh2'
    ),
    LogEntry(
        timestamp=datetime(2025, 7, 15, 10, 5, 0),
        hostname='host2',
        log_source='auth',
        message='sudo: user1 : TTY=pts/0 ; PWD=/home/user1 ; USER=root ; COMMAND=/usr/bin/apt update'
    ),
    LogEntry(
        timestamp=datetime(2025, 7, 15, 10, 10, 0),
        hostname='host1',
        log_source='syslog',
        message='kernel: some regular kernel message'
    )
]

# Sample YAML content for the rules file
SAMPLE_RULES_YAML = """
- name: "Failed Password"
  log_source: "auth"
  pattern: "%Failed password%"

- name: "Successful Sudo Command"
  log_source: "auth"
  pattern: "%COMMAND=%"

- name: "Kernel Messages"
  log_source: "syslog"
  pattern: "%kernel%"
"""

def test_run_analysis_with_findings(db_session, capsys):
    """Tests that the analyzer correctly finds and reports log entries based on rules."""
    # Add sample logs to the mock database session
    db_session.add_all(ANALYZER_LOGS)
    db_session.commit()

    # Mock the open() call to return our sample YAML rules
    with patch("builtins.open", mock_open(read_data=SAMPLE_RULES_YAML)):
        run_analysis(db_session)

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that alerts for all three rules were printed
    assert "ALERT [Failed Password]: Found 1 matching log entries!" in captured.out
    assert "ALERT [Successful Sudo Command]: Found 1 matching log entries!" in captured.out
    assert "ALERT [Kernel Messages]: Found 1 matching log entries!" in captured.out
    assert "- Time: 2025-07-15 10:00:00, Host: host1, Message: Failed password" in captured.out

def test_run_analysis_no_findings(db_session, capsys):
    """Tests that the analyzer reports nothing when no logs match the rules."""
    # Database is empty, so no logs should match

    with patch("builtins.open", mock_open(read_data=SAMPLE_RULES_YAML)):
        run_analysis(db_session)

    captured = capsys.readouterr()

    # Assert that no alerts were printed
    assert "ALERT" not in captured.out

def test_run_analysis_file_not_found(db_session, capsys):
    """Tests that the analyzer handles a missing rules file gracefully."""
    # Mock open() to raise FileNotFoundError
    with patch("builtins.open", mock_open()) as mocked_open:
        mocked_open.side_effect = FileNotFoundError

        run_analysis(db_session)

    captured = capsys.readouterr()

    # Assert that the specific error message is printed
    assert "Error: analysis_rules.yml not found" in captured.out
