import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from typing import List, Dict
import redis
import hashlib
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

Base = sa.orm.declarative_base()

class LogEntry(Base):
    __tablename__ = 'log_entries'
    id = sa.Column(sa.Integer, primary_key=True)
    hash_id = sa.Column(sa.String, unique=True, index=True) 
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

def _calculate_hash(entry_data: Dict) -> str:
    """Calculates a stable SHA256 hash for a log entry dictionary."""
    # We dump the dict to a JSON string with sorted keys to ensure the hash
    # is always the same for the same data, regardless of dict order.
    # We use a default converter for the datetime object.
    encoded_entry = json.dumps(entry_data, sort_keys=True, default=str).encode('utf-8')
    return hashlib.sha256(encoded_entry).hexdigest()

def save_log_entries(session, entries: List[Dict]):
    if not entries:
        print("\nNo new log entries to commit.")
        return

    unique_new_entries = {}
    
    # --- Deduplication Logic ---
    print("\nChecking for duplicate log entries...")
    hashes = [_calculate_hash(entry) for entry in entries]
    
    seen_hashes = redis_client.mget(hashes)

    for i, entry_data in enumerate(entries):
        if seen_hashes[i] is None:
            entry_hash = hashes[i]
            entry_data['hash_id'] = entry_hash
            unique_new_entries[entry_hash] = entry_data
    
    if not unique_new_entries:
        print("No new unique log entries found.")
        return

    new_log_objects = [LogEntry(**data) for data in unique_new_entries.values()]
        
    print(f"\nCommitting {len(new_log_objects)} new unique log entries to the database...")
    session.bulk_save_objects(new_log_objects)
    session.commit()
    print("Commit complete.")
    
    pipeline = redis_client.pipeline()
    for log_obj in new_log_objects:
        pipeline.set(log_obj.hash_id, '1')
    pipeline.execute()
    print(f"Updated Redis cache with {len(new_log_objects)} new hashes.")
