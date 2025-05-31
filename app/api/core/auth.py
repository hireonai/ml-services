"""
Authentication utilities for API endpoints.

This module provides authentication mechanisms for securing API endpoints
using a secret key approach.
"""

import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette import status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the API key header
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get the API key from environment variables
API_KEY = os.getenv("API_SECRET_KEY")
if not API_KEY:
    raise ValueError("API_SECRET_KEY environment variable is not set")


async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Validate the API key from the request headers.

    Args:
        api_key: The API key from the request header

    Returns:
        The API key if valid

    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header is missing",
        )

    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return api_key
