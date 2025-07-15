from sqlalchemy.orm import Session
from .database import LogEntry

def find_failed_logins(session: Session):

    query = session.query(LogEntry).filter(
        LogEntry.log_source == 'auth',
        LogEntry.message.like('%Failed password%')
    )
    
    failed_attempts = query.all()
    
    if not failed_attempts:
        print("\nNo failed login attempts found.")
        return

    print(f"\nALERT: Found {len(failed_attempts)} failed login attempts!")
    for attempt in failed_attempts:
        print(f"  - Time: {attempt.timestamp}, Host: {attempt.hostname}, Message: {attempt.message}")
