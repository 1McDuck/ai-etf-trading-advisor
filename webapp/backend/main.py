# webapp/backend/main.py
#
# FastAPI application entry point.
#
# Sets up the app, middleware and routers. The lifespan handler creates the
# TaskManager on startup and shuts it down cleanly when the server stops.
# The TaskManager holds the thread pool that runs backtests, regime detection
# and ranking jobs in the background without blocking the API.
#
# CORS is configured to allow requests from the React dev server on port 3000.
#
# !!! Run instructions: !!!!
#   uvicorn webapp.backend.main:app --reload

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from webapp.backend.api.routes_backtest import router as backtest_router
from webapp.backend.api.routes_health import router as health_router
from webapp.backend.api.routes_ranking import router as ranking_router
from webapp.backend.api.routes_regime import router as regime_router
from webapp.backend.services.task_manager import TaskManager


# Creates the TaskManager on startup, shuts it down when the server stops
# routes access it via request.app.state.task_manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.task_manager = TaskManager(max_workers=2)
    yield
    app.state.task_manager.shutdown()


app = FastAPI(
    title="AI ETF Advisor",
    version="1.0.0",
    lifespan=lifespan
)

# Allow the React frontend (localhost:3000) to make cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register all the routers
app.include_router(backtest_router)
app.include_router(health_router)
app.include_router(ranking_router)
app.include_router(regime_router)
