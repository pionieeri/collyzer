# Collyzer - Log Collector & Analyzer

Collyzer is a tool for collecting, parsing, and storing log files from remote systems for security analysis.

## Current Features

*   **Remote Log Collection:** Connects to multiple hosts via SSH to fetch log files (`/var/log/syslog`, `/var/log/auth.log`).
*   **Syslog Parsing:** Parses standard syslog and auth logs to extract structured data (timestamp, hostname, process, PID, message).
*   **SQLite Storage:** Stores parsed log entries in a local SQLite database for easy querying and analysis.
*   **Configuration-driven:** Uses a `.env` file to manage target hosts, credentials, and database paths.

## Getting Started

### 1. Development Environment

This project uses [Nix](https://nixos.org/) to provide a reproducible development environment.

To activate the environment, which includes all necessary dependencies, run:
```bash
nix develop
```

### 2. Running the Collector

The main application logic is in `src/main.py`. It requires a `.env` file in the root directory with the following variables:

```
HOST_IPS=192.168.1.10,192.168.1.11
SSH_USER=your_ssh_user
SSH_KEY_PATH=~/.ssh/id_rsa
SQLITE_DB_PATH=logs.db
```

Once the `.env` file is configured, run the application as a module using `uv`:

```bash
uv run python -m src.main
```

The collected logs will be stored in the SQLite file specified by `SQLITE_DB_PATH`. You can inspect the database using a tool like `datasette` (included in the development environment):

```bash
datasette logs.db
```
