# Collyzer - Log Collector & Analyzer

**This project is intended for educational purposes to explore concepts in automated security data pipelines and is not recommended for production use.**

Collyzer - currently - is a tool for collecting, parsing, and storing log files from remote systems for security analysis.

## Features

*   **Concurrent Remote Log Collection:** Fetches logs from multiple hosts via SSH in parallel.
*   **JSON Parsing:** Ingests and normalizes logs from systemd-journald JSON output.
*   **CIM-Compliant Schema:** Stores data in a structured format.
*   **SQLite Storage:** Stores parsed log entries in a local SQLite database.

## Getting Started

### Prerequisites

*   [Nix](https://nixos.org/download.html) must be installed on your system.
*   Passwordless SSH access (using key-based authentication) must be configured for the target hosts you wish to monitor.

### Installation & Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/pionieeri/collyzer
    cd collyzer
    ```

2.  **Enter the development environment:**
    This command uses `flake.nix` to provide all necessary tools like Python, `uv`, `just`, and `datasette`.
    ```bash
    nix develop
    ```

3.  **Install Python dependencies:**
    `uv` will install the packages defined in `pyproject.toml` into a virtual environment.
    ```bash
    uv sync
    ```

4.  **Configure the application:**
    Copy the example environment file and edit it with your specific details.
    ```bash
    cp .env.example .env
    ```
    Now, open `.env` and set the following variables:
    *   `HOST_IPS`: A comma-separated list of remote host IPs.
    *   `SSH_USER`: The username for SSH connections.
    *   `SSH_KEY_PATH`: The absolute path to your SSH private key (e.g., `~/.ssh/id_rsa`).
    *   `SQLITE_DB_PATH`: The path where the database file will be stored.

### 2. Running the Application

This project uses a `justfile` to provide simple commands for common tasks.

#### Run a Full Cycle

This is the primary command. It connects to remote hosts, fetches new logs, queues them, and processes the entire queue into the database.

```bash
just run
```
<details>
  <summary>Equivalent Python Command</summary>

  ```bash
  uv run python -m src.main
  ```
</details>

---

#### Run with Sample Data

To test the parsing and database logic without connecting to remote hosts, use the `sample` command. This will load logs from the `sample_logs/` directory into the queue.

```bash
just sample
```
<details>
  <summary>Equivalent Python Command</summary>

  ```bash
  uv run python -m src.main --use-sample-logs
  ```
</details>

## Inspecting the Data

Collected logs are stored in the SQLite file specified by `SQLITE_DB_PATH` (e.g., `logs.db`). The data is normalized into a CIM-compliant schema with fields like `action`, `app`, `user`, etc.

You can inspect the database with `datasette`:
```bash
datasette logs.db
```
