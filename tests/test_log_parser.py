import pytest
from datetime import datetime
from log_parser import parse_line

# 1. Test a standard syslog line from a CRON job
def test_parse_line_cron_job():
    log_line = "Jul 11 10:01:01 host1 CRON[12345]: (root) CMD (command)"
    current_year = datetime.now().year
    expected = {
        'timestamp': datetime(current_year, 7, 11, 10, 1, 1),
        'hostname': 'host1',
        'process_name': 'CRON',
        'pid': 12345,
        'message': '(root) CMD (command)'
    }
    assert parse_line(log_line) == expected

# 2. Test a line from auth.log with a process name but no PID
def test_parse_line_sshd_no_pid():
    log_line = "Jul 11 10:02:02 host1 sudo:    user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/apt update"
    current_year = datetime.now().year
    expected = {
        'timestamp': datetime(current_year, 7, 11, 10, 2, 2),
        'hostname': 'host1',
        'process_name': 'sudo',
        'pid': None,
        'message': 'user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/apt update'
    }
    assert parse_line(log_line) == expected

# 3. Test a completely malformed line
def test_parse_line_malformed():
    log_line = "this is not a valid syslog line at all"
    assert parse_line(log_line) is None

# 4. Test a line with a different timestamp format that should fail
def test_parse_line_bad_timestamp():
    log_line = "2023-07-11 10:01:01 host1 CRON[12345]: (root) CMD (command)"
    assert parse_line(log_line) is None

# 5. Test a line where the message part is empty
def test_parse_line_empty_message():
    log_line = "Jul 11 10:01:01 host1 CRON[12345]: "
    current_year = datetime.now().year
    expected = {
        'timestamp': datetime(current_year, 7, 11, 10, 1, 1),
        'hostname': 'host1',
        'process_name': 'CRON',
        'pid': 12345,
        'message': ''
    }
    assert parse_line(log_line) == expected
