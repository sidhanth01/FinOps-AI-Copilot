from fastapi import APIRouter
from app.models import HealthCheckResponse

router = APIRouter()

@router.get("/health", response_model=HealthCheckResponse, tags=["Service"])
def get_health_status():
    """
    Returns the status of the API. Used by Docker's healthcheck.
    """
    return {"status": "ok", "service": "finops-copilot-api"}