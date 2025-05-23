"""
API router initialization module.

This module configures and exports the main API router with all route handlers.
"""

from fastapi import APIRouter
from app.api.cv_job_ai_analyzer import router as cv_job_analyzer_router

# Create main API router
router = APIRouter()

# Include all routers
router.include_router(cv_job_analyzer_router)
