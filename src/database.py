import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List, Dict

Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "log_entries"
    # Core Identity & Context
    id = sa.Column(sa.Integer, primary_key=True)
    hostname = sa.Column(sa.String, index=True)
    timestamp = sa.Column(sa.DateTime, index=True)
    log_source = sa.Column(sa.String, index=True)
    process_name = sa.Column(sa.String, index=True)
    pid = sa.Column(sa.String, index=True, nullable=True)
    uid = sa.Column(sa.String, index=True, nullable=True)
    gid = sa.Column(sa.String, index=True, nullable=True)

    # Outcome
    action = sa.Column(sa.String, default='observed', index=True)
    status = sa.Column(sa.String, index=True, nullable=True)

    # Generic Payload Fields
    user = sa.Column(sa.String, index=True, nullable=True)
    src_ip = sa.Column(sa.String, index=True, nullable=True)
    dest_ip = sa.Column(sa.String, index=True, nullable=True)
    src_port = sa.Column(sa.Integer, nullable=True)
    dest_port = sa.Column(sa.Integer, nullable=True)
    command = sa.Column(sa.String, nullable=True)
    object = sa.Column(sa.String, nullable=True)

    # Original Message
    message = sa.Column(sa.String)

def init_db(db_path):
    engine = sa.create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def save_log_entries(session, entries: List[Dict]):
    if not entries:
        print("\nNo new log entries to save.")
        return

    new_log_objects = [LogEntry(**data) for data in entries]

    session.bulk_save_objects(new_log_objects)
