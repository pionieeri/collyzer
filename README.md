# Collyzer - Log Collector & Analyzer

Please be aware that this project is built solely for understanding various topics around automated security practices, and as such it is not suitable for any production use.

Collyzer is a tool for collecting, parsing, and storing log files from remote systems for security analysis.

## Features

*   **Concurrent Remote Log Collection:** Fetches logs from multiple hosts via SSH in parallel.
*   **JSON Parsing:** Ingests and normalizes logs from systemd-journald JSON output.
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

### 3. Running the Application

Collyzer can be run in two main ways: as a single end-to-end cycle or as separate, continuous services for collection and parsing.

*   **End-to-End Cycle (Default):**
    This is the standard mode. It fetches, parses, and analyzes logs in one go.
    ```bash
    # Fetch remote logs and process them
    just run
    # Or, using python directly:
    uv run python -m src.main
    ```

*   **Using Local Sample Logs:**
    To test the pipeline with local data instead of connecting to remote hosts:
    ```bash
    # Run the full cycle using logs from the `sample_logs/` directory
    just sample
    # Or, using python directly:
    uv run python -m src.main --use-sample-logs
    ```

*   **As Separate Services:**
    For continuous operation, you can run the collector and parser as independent services.
    ```bash
    # Terminal 1: Run the log collector service
    uv run python -m src.main --service collector

    # Terminal 2: Run the log parser service
    uv run python -m src.main --service parser
    ```


## Configuration

The analysis logic is controlled by `analysis_rules.yml`:

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
