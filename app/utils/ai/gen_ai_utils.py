"""
Utility functions specific to the Gen AI services.

This module provides helper functions for CV job analysis, cover letter generation,
and other AI-powered features.
"""

import re
import json
import logging
from google import genai
from google.genai import types

from app.utils.ai.system_prompt import (
    CV_JOB_ANALYSIS_SYSTEM_PROMPT,
    COVER_LETTER_GENERATION_SYSTEM_PROMPT,
    CV_TO_TEXT_SYSTEM_PROMPT,
)

# Configure logger
logger = logging.getLogger(__name__)


def format_job_details_for_cover_letter_generation(job_details):
    """Format job details into text format for the model."""
    logger.info("Formatting job details for cover letter: %s", job_details.job_position)
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


async def generate_cover_letter(
    client: genai.Client,
    cv_url: str,
    job_details_text: str,
    current_date: str,
    specific_request: str,  # Fixed spelling from "spesific" to "specific"
):
    """
    Generate a cover letter using Gemini model.

    Args:
        client: Initialized Gemini Vertex AI API client
        cv_url: URL to the CV PDF document
        job_details_text: Formatted job details as text
        current_date: Current date string for the cover letter
        specific_request: Additional customization requests from user

    Returns:
        Gemini API response containing the generated cover letter
    """
    logger.info("Generating cover letter with Gemini for date: %s", current_date)

    try:
        # Create PDF document reference from URL
        cv_document = types.Part.from_uri(file_uri=cv_url, mime_type="application/pdf")
        logger.debug("Created PDF document reference from URL: %s", cv_url)

        # Prepare content structure for Gemini API
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="CV content:"),
                    cv_document,
                    types.Part.from_text(text="Job Details json:"),
                    types.Part.from_text(text=job_details_text),
                    types.Part.from_text(text="Current Date:"),
                    types.Part.from_text(text=current_date),
                    types.Part.from_text(text="Specific Request:"),
                    types.Part.from_text(
                        text=specific_request if specific_request else ""
                    ),
                ],
            )
        ]
        logger.debug("Prepared content structure for Gemini API")

        # Define safety settings to allow necessary content generation
        safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ]

        # Configure generation parameters
        generate_content_config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for more deterministic output
            top_p=1,
            seed=0,  # Fixed seed for reproducible results
            max_output_tokens=65535,
            safety_settings=safety_settings,
            system_instruction=[
                types.Part.from_text(text=COVER_LETTER_GENERATION_SYSTEM_PROMPT)
            ],
        )
        logger.debug("Configured generation parameters")

        # Call Gemini API and return response
        logger.info("Sending request to Gemini API")
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=contents,
            config=generate_content_config,
        )
        logger.info("Successfully received response from Gemini API")
        return response

    except Exception as e:
        logger.error("Error generating cover letter: %s", str(e), exc_info=True)
        raise


def format_job_details_for_ai_jobs_analysis(job_details):
    """Format job details into text format for the model."""
    logger.info("Formatting job details for analysis: %s", job_details.job_position)

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
    logger.info("Analyzing CV with Gemini model")

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
    logger.info("Processing Gemini response, took %.2f seconds", processing_time)

    # Remove markdown code block formatting if present
    json_text = re.sub(r"^```json\s*|\s*```$", "", response_text, flags=re.MULTILINE)

    # Parse the JSON string into a Python dictionary
    result = json.loads(json_text)

    # Add processing time to the result
    result["processing_time_seconds"] = round(processing_time, 2)
    result["model"] = "gemini-2.5-flash-preview-04-17"

    logger.info(
        "Processed response with score: %s", result.get("cv_relevance_score", "N/A")
    )
    return result


def format_cover_letter_response(response_text):
    """
    Format the cover letter response from Gemini into structured HTML for PDF conversion.

    Args:
        response_text: The text response from Gemini API

    Returns:
        str: Formatted HTML content ready for PDF conversion
    """
    logger.info("Formatting cover letter response for PDF generation")

    # Remove markdown code block formatting if present
    # This will remove ```html at the start and ``` at the end
    content = response_text.strip()
    if content.startswith("```html"):
        content = content[7:]  # Remove ```html
        logger.info("Removed ```html prefix from response")
    elif content.startswith("```"):
        content = content[3:]  # Remove ```
        logger.info("Removed ``` prefix from response")

    if content.endswith("```"):
        content = content[:-3]  # Remove trailing ```
        logger.info("Removed trailing ``` from response")

    content = content.strip()  # Remove any extra whitespace
    logger.info("Formatted HTML content (length: %d characters)", len(content))

    return content


async def generate_text_representation_from_cv(client, cv_content: bytes) -> str:
    """Generate text representation from CV content using Gemini."""
    logger.info(
        "Generating text representation from CV, size: %d bytes", len(cv_content)
    )

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=[types.Part.from_bytes(data=cv_content, mime_type="application/pdf")],
        config=types.GenerateContentConfig(
            temperature=0.0,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            system_instruction=CV_TO_TEXT_SYSTEM_PROMPT,
        ),
    )

    logger.info("Successfully generated CV text representation")
    return response
