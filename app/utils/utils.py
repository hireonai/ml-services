"""
Utility functions for the application.

This module provides helper functions for CV job analysis, including
downloading files, formatting job details, and interacting with the Gemini AI API.
"""

import re
import json
import asyncio

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
    # Extract just the content from the response
    content = (
        response_text.text if hasattr(response_text, "text") else str(response_text)
    )

    # Use double curly braces to escape them in the template
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cover Letter</title>
    <style>
        @font-face {{
            font-family: 'Arial';
            src: local('Arial');
        }}
        
        @page {{
            size: A4;
            margin: 0;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #fff;
        }}

        .cover-letter {{
            background-color: #fff;
            padding: 30px;
            width: 210mm; /* A4 width */
            height: 297mm; /* A4 height */
            box-sizing: border-box;
            font-size: 11pt; /* Base font size */
        }}

        .sender-info {{
            margin-bottom: 20px;
        }}

        .sender-info h1 {{
            font-size: 24pt; /* Larger font for name */
            font-weight: bold;
            margin: 0 0 5px 0;
            color: #333;
        }}

        .sender-info p {{
            margin: 2px 0;
            font-size: 10pt;
            color: #555;
        }}

        .date {{
            text-align: right;
            margin-bottom: 20px;
            font-size: 11pt;
            color: #333;
        }}

        .recipient-info {{
            margin-bottom: 15px;
        }}

        .recipient-info p {{
            margin: 2px 0;
            font-size: 11pt;
            color: #333;
        }}
        .recipient-info .recipient-name {{
            font-weight: bold;
        }}

        .salutation {{
            margin-bottom: 15px;
            font-size: 11pt;
            color: #333;
        }}

        .body-paragraph {{
            margin-bottom: 12px;
            text-align: justify;
            font-size: 11pt;
            color: #333;
        }}

        .closing {{
            margin-top: 20px;
            margin-bottom: 5px;
            font-size: 11pt;
            color: #333;
        }}

        .signature {{
            font-size: 11pt;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="cover-letter">
        {content}
    </div>
</body>
</html>"""

    return html_template.format(content=content)
