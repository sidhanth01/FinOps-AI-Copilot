from fastapi import FastAPI
from app.api.routes import health, kpi, chat # <-- Importing all routers
from app.database import create_db_and_tables # Import to ensure it can be run manually if needed

# Define the root path for Streamlit access
STREAMLIT_HOST = "localhost:8501"

app = FastAPI(
    title="AI Cost & Insights Copilot API",
    description="Backend API for FinOps KPI computation and RAG services.",
    version="1.0.0",
)

# --- Include Routers ---
# These register the endpoints with the main FastAPI app.
app.include_router(health.router, prefix="/api")
app.include_router(kpi.router, prefix="/api")
app.include_router(chat.router, prefix="/api") 

@app.get("/", tags=["Root"])
def read_root():
    """
    Root endpoint directing users to the Streamlit UI.
    """
    return {
        "message": "Welcome to the AI Cost & Insights Copilot API. Go to the dashboard.",
        "dashboard_url": f"http://{STREAMLIT_HOST}"
    }

if __name__ == "__main__":
    # This block is for local host testing outside of Docker (if needed)
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)