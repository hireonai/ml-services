"""
Main application initialization module.

This module initializes the FastAPI application and configures routes.
"""

from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(title="ML Services API", description="API for machine learning services")

app.include_router(api_router)


@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.

    Returns:
        dict: A simple welcome message
    """
    return {"message": "Hello World"}
