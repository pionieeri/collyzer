import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Dict

# The declarative_base() function is now used to create the base class
Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "log_entries"
    id = sa.Column(sa.Integer, primary_key=True)
    hostname = sa.Column(sa.String, index=True)
    timestamp = sa.Column(sa.DateTime, index=True)

    # --- Simplified CIM Fields from Journald ---
    process_name = sa.Column(sa.String, index=True) # From _SYSTEMD_UNIT or _COMM
    pid = sa.Column(sa.String, index=True)
    uid = sa.Column(sa.String, index=True)
    gid = sa.Column(sa.String, index=True)
    message = sa.Column(sa.String)
    action = sa.Column(sa.String, default='observed', index=True)

    # --- Original Data and Source ---
    raw_message = sa.Column(sa.String)              # The original JSON log entry
    log_source = sa.Column(sa.String, index=True)   # Should be 'journald'

    def __repr__(self):
        return f"<LogEntry(hostname='{self.hostname}', timestamp='{self.timestamp}', process_name='{self.process_name}')>"

def init_db(db_path):
    """Initializes the database and returns a session and engine."""
    engine = sa.create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def save_log_entries(session, entries: List[Dict]):
    """
    Saves a list of parsed log entries to the database.
    Deduplication has been removed for simplicity in this version.
    """
    if not entries:
        print("\nNo new log entries to save.")
        return

    new_log_objects = [LogEntry(**data) for data in entries]

    print(f"\nSaving {len(new_log_objects)} new log entries to the database...")
    session.bulk_save_objects(new_log_objects)
    session.commit()
    print("Save complete.")
