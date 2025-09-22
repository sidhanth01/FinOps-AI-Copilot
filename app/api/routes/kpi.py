from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from datetime import date
from typing import List

from app.models import BillingRecord, KPIResponse
from app.database import get_session

router = APIRouter()

def get_last_n_months_spend(session: Session, n: int = 2) -> List[dict]:
    """Helper to get the cost and month for the last N months."""
    
    # Find the most recent month in the data
    latest_month = session.exec(
        select(func.max(BillingRecord.invoice_month))
    ).one_or_none()
    
    if not latest_month:
        return []

    # Get the last N unique months
    recent_months = session.exec(
        select(BillingRecord.invoice_month)
        .distinct()
        .order_by(BillingRecord.invoice_month.desc())
        .limit(n)
    ).all()
    
    if not recent_months:
        return []

    # Get total cost for these months
    spend_data = session.exec(
        select(
            BillingRecord.invoice_month,
            func.sum(BillingRecord.cost).label("total_cost")
        )
        .where(BillingRecord.invoice_month.in_(recent_months))
        .group_by(BillingRecord.invoice_month)
        .order_by(BillingRecord.invoice_month)
    ).all()
    
    return [
        {"month": record.invoice_month, "total_cost": record.total_cost}
        for record in spend_data
    ]

@router.get("/kpi", response_model=KPIResponse, tags=["Analytics"])
def get_kpi_metrics(session: Session = Depends(get_session)):
    """
    Computes and returns essential FinOps KPI metrics.
    """
    try:
        # 1. Get current and previous month's spend for trends
        spend_history = get_last_n_months_spend(session, n=2)
        
        if not spend_history:
             raise HTTPException(status_code=404, detail="No billing data found.")
        
        # Sort data to ensure correct order: [Previous Month, Current Month]
        spend_history.sort(key=lambda x: x['month'])
        
        current_month_data = spend_history[-1]
        current_month_spend = current_month_data['total_cost']
        
        previous_month_spend = spend_history[0]['total_cost'] if len(spend_history) > 1 else current_month_spend
        
        # 2. Compute Monthly Trend
        if previous_month_spend == 0:
            monthly_trend_percentage = 0.0 # Avoid division by zero
        else:
            monthly_trend_percentage = ((current_month_spend - previous_month_spend) / previous_month_spend) * 100

        # 3. Compute Savings Opportunities (Based on optimization score)
        # Assuming optimization_score is a percentage of cost that could be saved
        savings_opportunities = session.exec(
            select(func.sum(BillingRecord.cost * BillingRecord.optimization_score))
        ).one_or_none() or 0.0
        
        # 4. Compute Waste Metrics (Simple metric: total spend on low optimization score resources)
        # Defining "waste" as spend on resources with score < 0.3
        waste_metrics = session.exec(
            select(func.sum(BillingRecord.cost))
            .where(BillingRecord.optimization_score < 0.3)
            .where(BillingRecord.invoice_month == current_month_data['month'])
        ).one_or_none() or 0.0

        # 5. Get Top 5 Cost Drivers (by Service)
        top_5_cost_drivers = session.exec(
            select(
                BillingRecord.service,
                func.sum(BillingRecord.cost).label("total_cost")
            )
            .where(BillingRecord.invoice_month == current_month_data['month'])
            .group_by(BillingRecord.service)
            .order_by(func.sum(BillingRecord.cost).desc())
            .limit(5)
        ).all()

        return KPIResponse(
            total_monthly_spend=round(current_month_spend, 2),
            savings_opportunities=round(savings_opportunities, 2),
            waste_metrics=round(waste_metrics, 2),
            monthly_trend_percentage=round(monthly_trend_percentage, 2),
            top_5_cost_drivers=[
                {"service": item.service, "cost": round(item.total_cost, 2)}
                for item in top_5_cost_drivers
            ]
        )

    except Exception as e:
        print(f"Error computing KPI metrics: {e}")
        # Re-raise or return a generic error response
        raise HTTPException(status_code=500, detail="Internal server error while fetching KPIs.")