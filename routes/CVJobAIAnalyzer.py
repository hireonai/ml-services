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
import requests
import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Request, Query
from fastapi import Body
from pydantic import BaseModel, HttpUrl, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from starlette import status
from typing import List
from google.cloud import storage

from utils.system_prompt import CV_JOB_ANALYSIS_SYSTEM_PROMPT

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_CLOUD_STORAGE_SERVICE_ACCOUNT_PATH")


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


class JobDetails(BaseModel):
    url: str
    company_profile_src: str
    company_name: str
    job_position: str
    employment_type: str
    working_location_type: str
    working_location: str
    min_experience: str
    salary: str
    job_desc_list: List[str]
    job_qualification_list: List[str]


class CVJobAnalysisRequest(BaseModel):
    job_details: JobDetails
    cv_cloud_path: str  # Path to the file in GCS bucket (e.g., "user_cv/filename.pdf")
    
    class Config:
        arbitrary_types_allowed = True


# TODO: Add Course Recommender and Download Logic from Cloud Storage
@router.post("/", status_code=status.HTTP_200_OK)
async def get_cv_job_analysis_flash(
    request: Request, 
    data: CVJobAnalysisRequest = Body(...)
):
    """
    Analyze CV against job details using the Gemini AI model.

    Args:
        request (Request): The FastAPI request object.
        data (CVJobAnalysisRequest): The request body containing job details and CV path in Cloud Storage.

    Returns:
        dict: The analysis result including processing time and model used.
    """
    start_time = time.time()
    
    try:
        # Get file directly from Google Cloud Storage
        print(f"Fetching file from GCS path: {data.cv_cloud_path}")
        storage_client = storage.Client()
        bucket = storage_client.bucket("main-storage-hireon")
        blob = bucket.blob(data.cv_cloud_path)
        
        # Download file content as bytes
        user_cv_content = blob.download_as_bytes()
        print(f"Downloaded {len(user_cv_content)} bytes from Cloud Storage")
        
        # Format job details as formatted text for the model
        formatted_job_details = f"""
        Job Position: {data.job_details.job_position}
        Company: {data.job_details.company_name}
        Employment Type: {data.job_details.employment_type}
        Location: {data.job_details.working_location} ({data.job_details.working_location_type})
        Experience Required: {data.job_details.min_experience}
        Salary: {data.job_details.salary}
        
        Job Description:
        {chr(10).join(f"- {item}" for item in data.job_details.job_desc_list)}
        
        Qualifications:
        {chr(10).join(f"- {item}" for item in data.job_details.job_qualification_list)}
        """

        # Use the async client for non-blocking requests
        response = await request.app.state.client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=[
                types.Part.from_bytes(data=user_cv_content, mime_type="application/pdf"),
                formatted_job_details,
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
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise