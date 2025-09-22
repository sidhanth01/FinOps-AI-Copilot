import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, Session, SQLModel, select
from datetime import date, timedelta
import os
import pandas as pd
import time 
from typing import Dict, Any, Generator

# Import your FastAPI app and necessary modules
from app.main import app
from app.database import get_session
from app.models import BillingRecord, KPIResponse
# Import ingestion helpers locally
from app.ingestion import generate_synthetic_data, perform_quality_checks 


# --- 1. CONFIGURATION AND FIXTURES ---

# CRITICAL FIX: The database must be thread-safe for the TestClient
# We will use the disk-based DB and rely on the robust cleanup logic.
SQLITE_FILE_NAME = "test_finops_copilot.db"
test_engine = create_engine(
    f"sqlite:///{SQLITE_FILE_NAME}",
    connect_args={"check_same_thread": False} 
) 

def create_test_db(engine_to_use):
    SQLModel.metadata.create_all(engine_to_use)

@pytest.fixture(scope="module", name="db_session")
def db_session_fixture():
    """Provides a thread-safe, module-scoped session."""
    
    create_test_db(test_engine)
    
    # We explicitly manage the session lifetime for cleanup
    session = Session(test_engine)
    yield session
    
    # --- Cleanup Fix ---
    session.close() 
    test_engine.dispose() 
    time.sleep(0.1) # Wait briefly for the OS to release the file lock
    SQLModel.metadata.drop_all(test_engine)
    if os.path.exists(SQLITE_FILE_NAME):
        os.remove(SQLITE_FILE_NAME)


@pytest.fixture(scope="module", name="test_data_client")
def test_data_client_fixture(db_session: Session):
    """
    Populates the database once per module and provides the TestClient.
    """
    
    # 1. Ingest data using the fixture's session
    test_df = generate_synthetic_data(num_records=100, months_history=3)
    max_month = max(test_df['invoice_month'])
    test_df.loc[test_df['invoice_month'] == max_month, 'cost'] *= 10
    
    cleaned_df = perform_quality_checks(test_df)
    
    billing_records = []
    for _, row in cleaned_df.iterrows():
        record_data: Dict[str, Any] = row.drop(['owner', 'env', 'tags_json']).to_dict()
        billing_records.append(BillingRecord(**record_data))
        
    db_session.add_all(billing_records)
    db_session.commit() # Data is now committed to the persistent file
    
    # 2. Define the dependency override using the single test_engine
    # This is the standard, reliable way for TestClient to get a session
    def get_session_override() -> Generator[Session, None, None]:
        # This will open a new connection/session from the shared engine instance
        with Session(test_engine) as session:
            yield session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    
    yield client
    
    # 3. Teardown
    app.dependency_overrides.clear()


# --- 2. TEST CASES ---

def test_health_check(test_data_client: TestClient):
    """TEST 1: Verifies the API health check endpoint."""
    response = test_data_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "finops-copilot-api"}

def test_kpi_endpoint_response(test_data_client: TestClient):
    """TEST 2: Verifies the KPI API endpoint is accessible and returns valid data."""
    # This MUST now pass 200 OK
    response = test_data_client.get("/api/kpi")
    assert response.status_code == 200 
    data = response.json()
    assert "total_monthly_spend" in data
    assert "monthly_trend_percentage" in data
    assert data["monthly_trend_percentage"] > 100 

def test_manual_kpi_calculation(db_session: Session):
    """TEST 3: Verifies the KPI calculation logic works directly on the populated session."""

    # Data is already guaranteed to be in the session due to the fixture dependency
    total_records = db_session.exec(select(BillingRecord)).all()
    assert len(total_records) > 0 
    
    from app.api.routes.kpi import get_kpi_metrics
    kpi_response = get_kpi_metrics(session=db_session)
    
    assert isinstance(kpi_response, KPIResponse)
    assert kpi_response.monthly_trend_percentage > 100 
    assert kpi_response.total_monthly_spend > 0

def test_data_quality_check():
    """TEST 4: Verifies the data quality check (ETL) logic handles edge cases."""
    
    raw_data = {
        'invoice_month': [date(2025, 1, 1), date(2025, 1, 1)],
        'resource_id': ['res-1', None],
        'cost': [100.00, -50.00],
        'optimization_score': [0.5, 0.1],
        'account_id': ['acc-1', 'acc-2'],
        'subscription': ['sub-1', 'sub-2'],
        'service': ['EC2', 'S3'],
        'resource_group': ['rg-1', 'rg-2'],
        'region': ['us-east-1', 'us-east-2'],
        'usage_qty': [100, 50],
        'unit_cost': [1.0, 1.0],
        'owner': ['alice', 'bob'],
        'env': ['prod', 'dev'],
        'tags_json': ['{}', '{}']
    }
    df = pd.DataFrame(raw_data)
    
    from app.ingestion import perform_quality_checks 
    cleaned_df = perform_quality_checks(df)
    
    assert (cleaned_df['cost'] >= 0).all()
    assert len(cleaned_df) == 1