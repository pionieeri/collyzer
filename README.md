# Collyzer - Log Collector & Analyzer

Collyzer is a tool for collecting, parsing, and storing log files from remote systems for security analysis. It fetches logs concurrently, deduplicates them using Redis, and stores them in a local SQLite database.

## Features

*   **Concurrent Remote Log Collection:** Connects to multiple hosts via SSH to fetch log files (`/var/log/syslog`, `/var/log/auth.log`) in parallel.
*   **Log Deduplication:** Uses a Redis-backed cache to ensure that log entries are processed and stored only once, preventing duplicate data.
*   **Syslog Parsing:** Parses standard syslog and auth logs to extract structured data (timestamp, hostname, process, PID, message).
*   **SQLite Storage:** Stores parsed log entries in a local SQLite database for easy querying and analysis.
*   **Configuration-driven:** Uses a `.env` file to manage target hosts, credentials, and database paths.

## Getting Started

### 1. Prerequisites

*   **Redis:** A running Redis server instance is required for the log deduplication feature. The development environment will start one automatically.

### 2. Installation & Environment

This project uses [Nix](https://nixos.org/) to provide a reproducible development environment. This is the recommended way to get started.

1.  **Activate the environment:** This will install all necessary dependencies, including Python, `uv`, `redis`, and our development tools. It will also start a Redis server in the background if one isn't running.
    ```bash
    nix develop
    ```

2.  **Configure the application:** Create a `.env` file in the root of the project. You can copy the provided template:
    ```bash
    cp .env.example .env
    ```
    Now, edit the `.env` file with your specific host IPs, SSH user, and key path.

### 3. Running the Collector

Once the `.env` file is configured, run the application as a Python module:

```bash
uv run python -m src.main
```

To run using local sample logs for testing, use the `--use-sample-logs` flag:
```bash
uv run python -m src.main --use-sample-logs
```

### 4. Inspecting the Data

The collected logs will be stored in the SQLite file specified by `SQLITE_DB_PATH`. You can inspect the database using a tool like `datasette` (included in the development environment):

```bash
datasette logs.db
```

## Development

This project uses a few tools to ensure code quality and consistency.

*   **Linting & Formatting:** We use [Ruff](https://docs.astral.sh/ruff/) to lint and format the codebase.
    ```bash
    # Check for linting errors
    ruff check .
    # Format all files
    ruff format .
    ```
*   **Testing:** The test suite is run using `pytest`.
    ```bash
    uv run pytest
    ```
