import os
from sqlmodel import create_engine, Session

# Define the file path for the SQLite database
# This uses the 'sql_app.db' file created at the root of the project by our ingestion script.
SQLITE_FILE_NAME = "sql_app.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, SQLITE_FILE_NAME)}"

# Create the engine, which manages the connection pool
engine = create_engine(SQLITE_URL, echo=False)

def get_session():
    """Dependency function to get a database session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Creates the database file and all tables defined in the models."""
    from app.models import BillingRecord, ResourceMetadata # Import models here to register them
    print("Creating database and tables...")
    BillingRecord.metadata.create_all(engine)
    ResourceMetadata.metadata.create_all(engine)
    print("Database setup complete.")