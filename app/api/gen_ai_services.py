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

from app.api.models import CVJobAnalysisRequest, CoverLetterGeneratorRequest
from app.utils.utils import (
    download_user_cv,
    format_job_details_for_ai_jobs_analysis,
    format_job_details_for_cover_letter_generation,
    analyze_cv_with_gemini,
    process_gemini_response,
    generate_cover_letter,
    format_cover_letter_response,
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
    prefix="/gen-ai-services",
    tags=["gen-ai-services"],
    lifespan=lifespan,
)


@router.post("/cv_job_analysis_flash", status_code=status.HTTP_200_OK)
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
        formatted_job_details = format_job_details_for_ai_jobs_analysis(
            data.job_details
        )

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


@router.post("/cover_letter_generator", status_code=status.HTTP_200_OK)
async def cover_letter_generator(
    request: Request, data: CoverLetterGeneratorRequest = Body(...)
):
    """
    Generate a cover letter for a job application.
    """
    start_time = time.time()

    user_cv_content = await download_user_cv(
        request.app.state.storage_client, data.cv_cloud_path
    )

    formatted_job_details = format_job_details_for_cover_letter_generation(
        data.job_details
    )

    response = await generate_cover_letter(
        request.app.state.client,
        user_cv_content,
        formatted_job_details,
        "23 Mei 2025",
    )

    # Format the response into HTML
    html_content = response.text

    # Calculate processing time
    processing_time = time.time() - start_time

    # Save HTML and PDF content to Google Cloud Storage
    try:
        import asyncio
        from weasyprint import HTML
        import io

        timestamp = int(time.time())

        # Generate file names
        html_filename = f"debug_cover_letter_{timestamp}.html"
        pdf_filename = f"debug_cover_letter_{timestamp}.pdf"

        # Define cloud storage paths
        html_cloud_path = f"generated_cv/{html_filename}"
        pdf_cloud_path = f"generated_cv/{pdf_filename}"

        # Get bucket
        bucket = request.app.state.storage_client.bucket("main-storage-hireon")

        # Upload HTML file
        html_blob = bucket.blob(html_cloud_path)
        html_blob.upload_from_string(html_content, content_type="text/html")

        # Generate PDF and upload
        def generate_and_upload_pdf():
            # Generate PDF in memory
            pdf_buffer = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)

            # Upload PDF
            pdf_blob = bucket.blob(pdf_cloud_path)
            pdf_blob.upload_from_file(pdf_buffer, content_type="application/pdf")

            return pdf_blob.public_url

        # Run PDF generation and upload in a separate thread
        pdf_url = await asyncio.to_thread(generate_and_upload_pdf)

        # Get public URLs
        html_url = html_blob.public_url

        print(f"Files uploaded to Cloud Storage:\nHTML: {html_url}\nPDF: {pdf_url}")
        logging.info(
            f"Files uploaded to Cloud Storage:\nHTML: {html_url}\nPDF: {pdf_url}"
        )
    except Exception as e:
        print(f"Failed to upload files to Cloud Storage: {str(e)}")
        logging.error(f"Failed to upload files to Cloud Storage: {str(e)}")

    return {
        "html_content": html_content,
        "processing_time_seconds": round(processing_time, 2),
        "model": "gemini-2.5-pro-preview-05-06",
    }
