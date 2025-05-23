"""
Application entry point.

This module serves as the entry point for running the FastAPI application with uvicorn.
"""

import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
