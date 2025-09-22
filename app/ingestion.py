import os
import pandas as pd
from sqlmodel import Session, select
from datetime import date, timedelta
import random
import uuid

# Project-specific imports
from app.database import create_db_and_tables, engine
from app.models import BillingRecord, ResourceMetadata

# --- Configuration ---
NUM_RECORDS = 1500  # Target number of records
MONTHS_HISTORY = 8  # Generate data for 8 months
START_DATE = date(2024, 1, 1) # Start month for data generation
SERVICES = ['EC2', 'S3', 'RDS', 'Lambda', 'EKS', 'Azure VM', 'GCP Compute']
REGIONS = ['us-east-1', 'us-west-2', 'eu-central-1', 'asia-south-1']

def generate_synthetic_data(num_records: int, months_history: int) -> pd.DataFrame:
    """Generates synthetic cloud spend data."""
    print("Generating synthetic cloud spend data...")
    data = {
        'invoice_month': [],
        'account_id': [],
        'subscription': [],
        'service': [],
        'resource_group': [],
        'resource_id': [],
        'region': [],
        'usage_qty': [],
        'unit_cost': [],
        'cost': [],
        'owner': [],
        'env': [],
        'tags_json': [],
        'optimization_score': []
    }

    # Generate months
    months = [START_DATE + timedelta(days=30 * i) for i in range(months_history)]
    
    # Introduce a cost spike in the 5th month (e.g., May) for anomaly detection
    spike_month = months[4] if len(months) > 4 else months[-1]

    for _ in range(num_records):
        month = random.choice(months)
        
        # Base cost generation
        unit_cost = random.uniform(0.001, 0.5)
        usage_qty = random.randint(10, 5000)
        cost = usage_qty * unit_cost
        
        # Introduce spike logic for a specific month and service (e.g., EC2)
        if month == spike_month and random.random() < 0.3: # 30% of EC2 records in spike month
            if random.choice(SERVICES) == 'EC2':
                cost *= random.uniform(1.5, 3.0) # 50% to 3x cost increase
        
        # Optimization score (for RAG data)
        optimization_score = round(random.uniform(0.1, 0.95), 2)
        
        # Populate data dict
        resource_id = str(uuid.uuid4())
        data['invoice_month'].append(month.replace(day=1))
        data['account_id'].append(f"ACC-{random.randint(100, 999)}")
        data['subscription'].append(f"Sub-{random.choice(['Prod', 'Dev', 'Test'])}")
        data['service'].append(random.choice(SERVICES))
        data['resource_group'].append(f"RG-{random.randint(1, 10)}")
        data['resource_id'].append(resource_id)
        data['region'].append(random.choice(REGIONS))
        data['usage_qty'].append(usage_qty)
        data['unit_cost'].append(unit_cost)
        data['cost'].append(cost)
        data['optimization_score'].append(optimization_score)
        
        # Metadata fields
        data['owner'].append(random.choice(['alice', 'bob', 'charlie', None]))
        data['env'].append(random.choice(['prod', 'staging', 'dev']))
        data['tags_json'].append(
            str({"Project": f"P-{random.randint(1, 5)}", "CostCenter": f"CC-{random.randint(10, 50)}"})
        )
        
    return pd.DataFrame(data)

def perform_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Performs required data quality checks."""
    print("Performing data quality checks...")
    
    # Check 1: Nulls in critical fields
    df = df.dropna(subset=['resource_id', 'cost'])
    
    # Check 2: Negative Costs (Treating as an anomaly, setting to 0 or dropping)
    if (df['cost'] < 0).any():
        print("  - WARNING: Negative costs found. Setting to 0.")
        df['cost'] = df['cost'].clip(lower=0)
        
    # Check 3: Duplicate Resource IDs (Only check resource metadata integrity)
    # We will let duplicates exist in billing (as multiple monthly records),
    # but ensure metadata is unique before insertion.
    
    print(f"Quality checks complete. Final records: {len(df)}")
    return df

def ingest_data(df: pd.DataFrame):
    """Loads the DataFrame into the SQLite database."""
    print("Starting data ingestion...")
    
    # 1. Prepare Metadata and Billing Records
    
    # Unique Resource IDs for Metadata
    metadata_df = df[['resource_id', 'owner', 'env', 'tags_json']].drop_duplicates(subset=['resource_id'])
    
    billing_records = []
    for _, row in df.iterrows():
        # Create a BillingRecord instance
        billing_record = BillingRecord(
            invoice_month=row['invoice_month'],
            account_id=row['account_id'],
            subscription=row['subscription'],
            service=row['service'],
            resource_group=row['resource_group'],
            resource_id=row['resource_id'],
            region=row['region'],
            usage_qty=row['usage_qty'],
            unit_cost=row['unit_cost'],
            cost=row['cost'],
            optimization_score=row['optimization_score']
        )
        billing_records.append(billing_record)
        
    # Create Metadata instances
    metadata_records = []
    for _, row in metadata_df.iterrows():
        # Create a ResourceMetadata instance
        metadata_record = ResourceMetadata(
            resource_id=row['resource_id'],
            owner=row['owner'],
            env=row['env'],
            tags_json=row['tags_json']
        )
        metadata_records.append(metadata_record)

    # 2. Load data into the database
    with Session(engine) as session:
        # Load metadata first (since billing depends on it via implied relationship)
        session.add_all(metadata_records)
        session.commit()
        
        # Load billing data
        session.add_all(billing_records)
        session.commit()
        print(f"Successfully ingested {len(billing_records)} billing records and {len(metadata_records)} resource metadata records.")

if __name__ == "__main__":
    # Ensure the database file and tables exist
    create_db_and_tables()
    
    # Generate, check, and ingest data
    synthetic_df = generate_synthetic_data(NUM_RECORDS, MONTHS_HISTORY)
    cleaned_df = perform_quality_checks(synthetic_df)
    ingest_data(cleaned_df)
    
    # Save the raw data for RAG vectorization in the next step
    cleaned_df.to_csv("data/synthetic_data.csv", index=False)
    print("Data ingestion pipeline finished.")