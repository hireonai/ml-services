"""
Main application package.
"""

from fastapi import FastAPI
from app.api.routes import router

# Create FastAPI application
app = FastAPI(
    title="ML Services API",
    description="API for AI and recommendation services",
    version="1.0.0",
)

# Include API router
app.include_router(router, prefix="/api")
