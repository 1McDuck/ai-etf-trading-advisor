# webapp/backend/main.py

from fastapi import FastAPI

from api.routes_health import router as health_router

app = FastAPI()

app.include_router(health_router)
    