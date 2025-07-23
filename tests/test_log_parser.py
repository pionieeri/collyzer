import pytest
from unittest.mock import mock_open, patch
from src.log_parser import LogParser
from datetime import datetime

# Sample YAML for parsing rules to be used in tests
SAMPLE_PARSING_RULES_YAML = """
- name: "SSH Session Opened"
  log_source: "auth"
  parsing_method: "regex"
  regex: 'session opened for user (?P<user>\\S+)'
  cim_mapping:
    action: "success"
    app: "sshd"
    category: "authentication"
    user: "{user}"

- name: "Sudo Command Execution"
  log_source: "auth"
  parsing_method: "regex"
  regex: 'USER=(?P<effective_user>\\S+)\\s+; COMMAND=(?P<command>.+)'
  cim_mapping:
    action: "success"
    app: "sudo"

- name: "Systemd JSON Log"
  log_source: "journal"
  parsing_method: "json"
  cim_mapping:
    app: "{_SYSTEMD_UNIT}"
    hostname: "{_HOSTNAME}"
"""

@pytest.fixture
def mock_rules_file(monkeypatch):
    """Mocks the open() call to provide the test YAML rules."""
    mock_file = mock_open(read_data=SAMPLE_PARSING_RULES_YAML)
    monkeypatch.setattr("builtins.open", mock_file)

@pytest.fixture
def parser(mock_rules_file):
    """Returns an instance of LogParser initialized with mocked rules."""
    return LogParser()

# --- Test Cases ---

def test_regex_parsing_success(parser):
    """Tests that a standard syslog line is correctly parsed by a regex rule."""
    log_line = "Jul 16 10:00:01 my-host sshd[1234]: session opened for user root"
    result = parser.parse(log_line, "auth")

    assert result["action"] == "success"
    assert result["app"] == "sshd"
    assert result["user"] == "root"
    assert result["hostname"] == "my-host"
    assert result["raw_message"] == log_line

def test_json_parsing_success(parser):
    """Tests that a JSON log line is correctly parsed by a JSON rule."""
    log_line = '{"_SYSTEMD_UNIT": "cron.service", "_HOSTNAME": "dev-server", "MESSAGE": "some message"}'
    result = parser.parse(log_line, "journal")

    assert result["app"] == "cron.service"
    assert result["hostname"] == "dev-server"
    assert result["raw_message"] == log_line

def test_parsing_fallback_unparsed(parser):
    """Tests that a line matching no rules results in an 'unparsed' action."""
    log_line = "Jul 16 10:05:00 my-host kernel: A generic kernel message"
    result = parser.parse(log_line, "auth") # Using 'auth' source where this won't match

    assert result["action"] == "unparsed"
    assert result["raw_message"] == log_line
    assert result["hostname"] == "my-host"

def test_year_rollover_heuristic(parser):
    """Tests that the timestamp parser correctly handles year-end rollover."""
    # Simulate that today is Jan 5, 2025, but the log is from Dec 31
    with patch('src.log_parser.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 1, 5, 12, 0, 0)
        mock_dt.strptime = datetime.strptime # Allow original strptime to work

        log_line = "Dec 31 23:59:59 host1 sshd[1234]: session opened for user test"
        result = parser.parse(log_line, "auth")
        
        assert result["timestamp"].year == 2024
        assert result["timestamp"].month == 12
        assert result["timestamp"].day == 31

def test_initialization_file_not_found():
    """Tests that the parser raises an error if the rules file is not found."""
    with patch("builtins.open", mock_open()) as mocked_open:
        mocked_open.side_effect = FileNotFoundError
        with pytest.raises(FileNotFoundError):
            LogParser()