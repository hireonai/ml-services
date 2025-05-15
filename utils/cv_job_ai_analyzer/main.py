"""
Module for CV Job Analysis using Gemini AI.

This module provides an API endpoint to analyze CVs against job details
using the Gemini AI model.
"""

import os
from contextlib import asynccontextmanager
import time
import re
import json

from fastapi import APIRouter, UploadFile, File, Request, Query
from dotenv import load_dotenv
from google import genai
from google.genai import types
from starlette import status

from ..system_prompt import CV_JOB_ANALYSIS_SYSTEM_PROMPT

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


@asynccontextmanager
async def lifespan(application: APIRouter):
    """
    Lifespan context manager for initializing and shutting down the Gemini client.

    This function sets up the Gemini client during the startup phase and
    cleans up resources during the shutdown phase.
    """
    # Startup logic
    application.state.client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini client initialized")
    yield
    # Shutdown logic


router = APIRouter(
    prefix="/cv-job-ai-analyzer",
    tags=["cv-job-ai-analyzer"],
    lifespan=lifespan,
)


# TODO: Add Course Recommender and Download Logic from Cloud Storage
@router.post("/", status_code=status.HTTP_200_OK)
async def get_cv_job_analysis_flash(
    request: Request, job_details: str = Query(...), user_cv: UploadFile = File(...)
):
    """
    Analyze CV against job details using the Gemini AI model.

    Args:
        job_details (str): The job details to analyze against.
        request (Request): The FastAPI request object.
        user_cv (UploadFile): The uploaded CV file.

    Returns:
        dict: The analysis result including processing time and model used.
    """
    start_time = time.time()

    # Read file content asynchronously
    user_cv_content = await user_cv.read()

    # Use the async client for non-blocking requests
    response = await request.app.state.client.aio.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=[
            types.Part.from_bytes(data=user_cv_content, mime_type=user_cv.content_type),
            job_details,
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            temperature=0.0,
            system_instruction=CV_JOB_ANALYSIS_SYSTEM_PROMPT,
        ),
    )

    # Calculate processing time
    processing_time = time.time() - start_time

    # Extract the JSON from the response
    # Remove markdown code block formatting if present
    text = response.text
    json_text = re.sub(r"^```json\s*|\s*```$", "", text, flags=re.MULTILINE)

    # Parse the JSON string into a Python dictionary
    result = json.loads(json_text)

    # Add processing time to the result
    result["processing_time_seconds"] = round(processing_time, 2)
    result["model"] = "gemini-2.5-flash-preview-04-17"

    return result
