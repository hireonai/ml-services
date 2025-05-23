"""
Utility functions for the application.

This module provides helper functions for CV job analysis, including
downloading files, formatting job details, and interacting with the Gemini AI API.
"""

import re
import json
import asyncio
import io
import time
from weasyprint import HTML

from google.genai import types

from app.utils.system_prompt import (
    CV_JOB_ANALYSIS_SYSTEM_PROMPT,
    COVER_LETTER_GENERATION_SYSTEM_PROMPT,
)


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


def format_job_details_for_cover_letter_generation(job_details):
    """Format job details into text format for the model."""
    return f"""
    Jobs URL: {job_details.url}
    Company Name: {job_details.company_name}
    Job Position: {job_details.job_position}
    Experience Required: {job_details.min_experience}
    Working Location: {job_details.working_location}
    Company Location: {job_details.company_location}
    
    Job Description:
    {chr(10).join(f"- {item}" for item in job_details.job_desc_list)}
    
    Job Qualifications:
    {chr(10).join(f"- {item}" for item in job_details.job_qualification_list)}
    """


async def generate_cover_letter(client, cv_content, job_details_text, current_date):
    """Generate a cover letter using Gemini."""
    return await client.aio.models.generate_content(
        model="gemini-2.5-pro-preview-05-06",
        contents=[
            types.Part.from_bytes(data=cv_content, mime_type="application/pdf"),
            job_details_text,
            f"Current Date: {current_date}",
        ],
        config=types.GenerateContentConfig(
            temperature=0.0,
            system_instruction=COVER_LETTER_GENERATION_SYSTEM_PROMPT,
        ),
    )


def format_job_details_for_ai_jobs_analysis(job_details):
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


def format_cover_letter_response(response_text):
    """
    Format the cover letter response from Gemini into structured HTML for PDF conversion.

    Args:
        response_text: The text response from Gemini API

    Returns:
        str: Formatted HTML content ready for PDF conversion
    """

    # Remove markdown code block formatting if present
    # This will remove ```html at the start and ``` at the end
    content = response_text.strip()
    if content.startswith("```html"):
        content = content[7:]  # Remove ```html
    elif content.startswith("```"):
        content = content[3:]  # Remove ```

    if content.endswith("```"):
        content = content[:-3]  # Remove trailing ```

    content = content.strip()  # Remove any extra whitespace

    return content


async def generate_and_upload_pdf(
    storage_client, html_content, filename_prefix="cover_letter"
):
    """
    Generate PDF from HTML content and upload it to Google Cloud Storage.

    Args:
        storage_client: Google Cloud Storage client
        html_content: HTML content to convert to PDF
        filename_prefix: Prefix for the generated filename

    Returns:
        dict: Contains PDF URL and filename
    """

    timestamp = int(time.time())
    pdf_filename = f"{filename_prefix}_{timestamp}.pdf"
    pdf_cloud_path = f"generated_cv/{pdf_filename}"

    # Get bucket
    bucket = storage_client.bucket("main-storage-hireon")

    # Generate PDF and upload
    def generate_and_upload():
        # Generate PDF in memory
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        # Upload PDF
        pdf_blob = bucket.blob(pdf_cloud_path)
        pdf_blob.upload_from_file(pdf_buffer, content_type="application/pdf")

        # Make the blob publicly accessible
        pdf_blob.make_public()

        # Get the public URL
        public_url = pdf_blob.public_url

        return {
            "pdf_url": public_url,
            "pdf_cloud_path": pdf_cloud_path,
            "pdf_filename": pdf_filename,
        }

    # Run PDF generation and upload in a separate thread
    result = await asyncio.to_thread(generate_and_upload)

    return result
