from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, ForeignKey # <-- Ensure ForeignKey is imported
from datetime import date
from pydantic import BaseModel

# --- Database Models (Mapping to SQLIte tables) ---

class BillingRecordBase(SQLModel):
    """Base model for Billng records, containing shared fields."""
    invoice_month: date = Field(index=True)
    account_id: str
    subscription: str = Field(index=True)
    service: str = Field(index=True)
    resource_group: str
    
    # -------------------------------------------------------------------
    # FIX 1: Add ForeignKey to link to the ResourceMetadata table's ID
    # -------------------------------------------------------------------
    resource_id: str = Field(index=True, foreign_key="resourcemetadata.resource_id") 
    # NOTE: The table name is lowercase and singular by convention: resourcemetadata
    
    region: str
    usage_qty: float
    unit_cost: float
    cost: float = Field(index=True)
    optimization_score: float = Field(default=0.0)

class BillingRecord(BillingRecordBase, table=True):
    """The main table model for cloud spend data."""
    id: Optional[int] = Field(default=None, primary_key=True)

    # Define the relationship to ResourceMetadata
    # The back_populates ensures a bidirectional relationship
    resource_meta: Optional["ResourceMetadata"] = Relationship(back_populates="billing_records")


class ResourceMetadataBase(SQLModel):
    """Base model for static resource data."""
    # -------------------------------------------------------------------
    # FIX 2: Ensure the linked column is unique, so it can be a foreign key target
    # -------------------------------------------------------------------
    resource_id: str = Field(index=True, unique=True) # <-- Added unique=True
    owner: Optional[str] = Field(default="Unknown")
    env: Optional[str] = Field(default="staging")
    tags_json: Optional[str] 

class ResourceMetadata(ResourceMetadataBase, table=True):
    """The resource metadata table."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship to billing records
    # back_populates is the name of the field in the other model (BillingRecord)
    billing_records: Optional[list[BillingRecord]] = Relationship(back_populates="resource_meta")

# --- Pydantic Schemas (No changes needed below this line) ---
class HealthCheckResponse(BaseModel):
    """Schema for the /health response."""
    status: str
    service: str

class KPIData(BaseModel):
    """Schema for individual KPI objects."""
    metric: str
    value: float
    unit: str
    trend_vs_previous_month: Optional[float] = None 

class KPIResponse(BaseModel):
    """Schema for the main KPI API response."""
    status: str = "success"
    total_monthly_spend: float
    savings_opportunities: float
    waste_metrics: float
    monthly_trend_percentage: float
    top_5_cost_drivers: list[dict]