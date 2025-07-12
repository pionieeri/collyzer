import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from typing import List, Dict

Base = sa.orm.declarative_base()

class LogEntry(Base):
    __tablename__ = 'log_entries'
    id = sa.Column(sa.Integer, primary_key=True)
    hostname = sa.Column(sa.String, index=True)
    timestamp = sa.Column(sa.DateTime, index=True)
    process_name = sa.Column(sa.String, index=True)
    pid = sa.Column(sa.Integer, nullable=True)
    message = sa.Column(sa.String)
    log_source = sa.Column(sa.String, index=True)

    def __repr__(self):
        return f"<LogEntry(hostname='{self.hostname}', timestamp='{self.timestamp}', message='{self.message[:30]}...')>"

def init_db(db_path):
    engine = sa.create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def save_log_entries(session, entries: List[Dict]):
    if not entries:
        print("\nNo new log entries to commit.")
        return

    print(f"\nCommitting {len(entries)} new log entries to the database...")
    for entry_data in entries:
        entry = LogEntry(**entry_data)
        session.add(entry)
    
    session.commit()
    print("Commit complete.")

