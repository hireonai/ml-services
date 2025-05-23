"""
Utility functions for the application.

This module provides helper functions for CV job analysis, including
downloading files, formatting job details, and interacting with the Gemini AI API.
"""

import re
import json
import asyncio

from google.genai import types

from app.utils.system_prompt import CV_JOB_ANALYSIS_SYSTEM_PROMPT


async def download_user_cv(storage_client, cv_cloud_path: str) -> bytes:
    """
    Download a CV file from Google Cloud Storage.

    Args:
        storage_client: Google Cloud Storage client
        cv_cloud_path: Path to the CV file in Cloud Storage

    Returns:
        bytes: The CV file content as bytes
    """

    print("Fetching file from GCS path: %s", cv_cloud_path)
    bucket = storage_client.bucket("main-storage-hireon")
    blob = bucket.blob(cv_cloud_path)

    # Download file content as bytes asynchronously
    user_cv_content = await asyncio.to_thread(blob.download_as_bytes)
    print("Downloaded %d bytes from Cloud Storage", len(user_cv_content))

    return user_cv_content


def format_job_details(job_details):
    """Format job details into text format for the model."""
    return f"""
    Job Position: {job_details.job_position}
    Experience Required: {job_details.min_experience}
    
    Job Description:
    {chr(10).join(f"- {item}" for item in job_details.job_desc_list)}
    
    Qualifications:
    {chr(10).join(f"- {item}" for item in job_details.job_qualification_list)}
    """


async def analyze_cv_with_gemini(client, cv_content, job_details_text):
    """Send CV and job details to Gemini for analysis."""
    return await client.aio.models.generate_content(
        model="gemini-2.5-flash-preview-04-17",
        contents=[
            types.Part.from_bytes(data=cv_content, mime_type="application/pdf"),
            job_details_text,
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            temperature=0.0,
            system_instruction=CV_JOB_ANALYSIS_SYSTEM_PROMPT,
        ),
    )


def process_gemini_response(response_text, processing_time):
    """Process Gemini response and extract JSON result."""
    # Remove markdown code block formatting if present
    json_text = re.sub(r"^```json\s*|\s*```$", "", response_text, flags=re.MULTILINE)

    # Parse the JSON string into a Python dictionary
    result = json.loads(json_text)

    # Add processing time to the result
    result["processing_time_seconds"] = round(processing_time, 2)
    result["model"] = "gemini-2.5-flash-preview-04-17"

    return result
