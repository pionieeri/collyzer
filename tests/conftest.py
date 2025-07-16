import pytest
from src.database import init_db

@pytest.fixture
def db_session():
    """Creates a new in-memory SQLite database session for each test."""
    session, _ = init_db(':memory:')
    yield session
    session.close()
