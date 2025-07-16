from sqlalchemy import text

VIEW_SUDO_USAGE = """
CREATE VIEW IF NOT EXISTS sudo_usage AS
SELECT
    timestamp,
    hostname,
    message
FROM log_entries
WHERE
    log_source = 'auth' AND process_name = 'sudo' AND message LIKE '%COMMAND=%';
"""

VIEW_LOG_COUNT_BY_HOUR = """
CREATE VIEW IF NOT EXISTS log_count_by_hour AS
SELECT
    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
    hostname,
    log_source,
    count(*) as log_count
FROM log_entries
GROUP BY hour, hostname, log_source
ORDER BY hour DESC;
"""

def create_summary_views(engine):
    """Executes all CREATE VIEW statements against the database."""
    print("\nCreating/Updating summary views...")
    with engine.connect() as connection:
        connection.execute(text(VIEW_SUDO_USAGE))
        connection.execute(text(VIEW_LOG_COUNT_BY_HOUR))
    print("Views created successfully.")
