"""
Routes package containing all API endpoints.
"""

from fastapi import APIRouter
from app.api.routes.gen_ai_services import router as gen_ai_services_router
from app.api.routes.recommendation_engine_services import (
    router as recommendation_engine_services_router,
)

# Create main API router
router = APIRouter()

# Include all routers
router.include_router(gen_ai_services_router)
router.include_router(recommendation_engine_services_router)
