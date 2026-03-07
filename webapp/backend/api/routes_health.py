#webapp/backend/api/routes_health.py

# Health check endpoint to verify the API is running

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/api/health")
def health_check():
    return {"status": "ok"}
