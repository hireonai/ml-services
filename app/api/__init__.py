from fastapi import APIRouter

# Create main API router
router = APIRouter()

# Import routers from endpoint modules
from app.api.CVJobAIAnalyzer import router as cv_job_analyzer_router

# Include all routers
router.include_router(cv_job_analyzer_router)