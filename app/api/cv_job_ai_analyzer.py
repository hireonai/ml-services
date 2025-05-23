"""
Module for CV Job Analysis using Gemini AI.

This module provides an API endpoint to analyze CVs against job details
using the Gemini AI model.
"""

import os
from contextlib import asynccontextmanager
import time
import logging

from fastapi import APIRouter, Request, Body
from dotenv import load_dotenv
from google import genai
from google.cloud import storage
from starlette import status

from app.api.models import CVJobAnalysisRequest
from app.utils.utils import (
    download_user_cv,
    format_job_details,
    analyze_cv_with_gemini,
    process_gemini_response,
)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if os.getenv("GOOGLE_CLOUD_STORAGE_SERVICE_ACCOUNT_PATH"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv(
        "GOOGLE_CLOUD_STORAGE_SERVICE_ACCOUNT_PATH"
    )
else:
    # Default path inside container
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
        "credentials/google_cloud_storage_service_account.json"
    )


@asynccontextmanager
async def lifespan(application: APIRouter):
    """
    Lifespan context manager for initializing and shutting down the Gemini client.

    This function sets up the Gemini client during the startup phase and
    cleans up resources during the shutdown phase.
    """
    # Startup logic
    application.state.client = genai.Client(api_key=GEMINI_API_KEY)
    application.state.storage_client = storage.Client()
    print("Gemini client and storage client initialized")
    yield
    # Shutdown logic


router = APIRouter(
    prefix="/cv-job-ai-analyzer",
    tags=["cv-job-ai-analyzer"],
    lifespan=lifespan,
)


@router.post("/", status_code=status.HTTP_200_OK)
async def get_cv_job_analysis_flash(
    request: Request, data: CVJobAnalysisRequest = Body(...)
):
    """
    Analyze CV against job details using the Gemini AI model.
    """
    start_time = time.time()

    try:
        # Get file directly from Google Cloud Storage asynchronously
        user_cv_content = await download_user_cv(
            request.app.state.storage_client, data.cv_cloud_path
        )

        # Format job details as formatted text for the model
        formatted_job_details = format_job_details(data.job_details)

        # Use the async client for non-blocking requests
        response = await analyze_cv_with_gemini(
            request.app.state.client, user_cv_content, formatted_job_details
        )

        # Process response
        result = process_gemini_response(response.text, time.time() - start_time)

        return result

    except Exception as e:
        logging.info("Error occurred: %s", str(e))
        raise
