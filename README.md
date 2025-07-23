# Collyzer - Log Collector & Analyzer

Please be aware, that this project is build solely for understanding various topics around automated security practices, and as such it is not suitable for any production use.

Collyzer is a tool for collecting, parsing, and storing log files from remote systems for security analysis.

## Features

*   **Concurrent Remote Log Collection:** Fetches logs from multiple hosts via SSH in parallel.
*   **YAML-Driven Parsing:** Ingests and normalizes logs using a multi-method parser (`regex`, `json`) configured in `parsing_rules.yml`.
*   **CIM-Compliant Schema:** Stores data in a structured format for powerful, cross-source querying.
*   **Rule-Based Analysis:** Scans the normalized database for patterns defined in `analysis_rules.yml`.
*   **Log Deduplication:** Uses a Redis-backed cache to prevent duplicate entries.
*   **SQLite Storage:** Stores parsed log entries in a local SQLite database.

## Getting Started

### 1. Prerequisites

*   **Redis:** A running Redis server instance is required. The development environment starts one automatically.

### 2. Installation & Environment

This project uses [Nix](https://nixos.org/) for a reproducible development environment.

1.  **Activate the environment:**
    ```bash
    nix develop
    ```
2.  **Configure the application:** Copy the example `.env` file and edit it with your host IPs, SSH user, and key path.
    ```bash
    cp .env.example .env
    ```

### 3. Running the Collector

```bash
# Fetch remote logs
uv run python -m src.main

# Use local sample logs for testing
uv run python -m src.main --use-sample-logs
```

## Configuration

The parsing and analysis logic is controlled by two YAML files:

*   **`parsing_rules.yml`**: Defines how to parse different log sources.
    ```yaml
    # Example:
    - name: "SSH Session Opened"
      log_source: "auth"
      parsing_method: "regex"
      regex: 'session opened for user (?P<user>\S+)'
      cim_mapping:
        action: "success"
        app: "sshd"
        user: "{user}"
    ```

*   **`analysis_rules.yml`**: Defines queries to find specific events in the normalized data.
    ```yaml
    # Example:
    - name: "SSH Authentication Failure"
      query_filters:
        action: "failure"
        app: "sshd"
    ```

## Inspecting the Data

Collected logs are stored in the SQLite file specified by `SQLITE_DB_PATH` (e.g., `logs.db`). The data is normalized into a CIM-compliant schema with fields like `action`, `app`, `user`, etc.

You can inspect the database with `datasette`:
```bash
datasette logs.db
```

## Development

*   **Linting & Formatting:**
    ```bash
    ruff check . && ruff format .
    ```
*   **Testing:**
    ```bash
    uv run pytest
    ```
