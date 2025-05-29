"""
Main application package.
"""

import logging
import sys
from fastapi import FastAPI
from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        # You can add a file handler here if you also want logs in a file
        # logging.FileHandler("app.log"),
    ],
)

# Create FastAPI application
app = FastAPI(
    title="ML Services API",
    description="API for AI and recommendation services",
    version="1.0.0",
)

# Include API router
app.include_router(router, prefix="/api")
