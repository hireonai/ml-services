"""
Module for CV Job Analysis using Gemini AI.

This module provides an API endpoint to analyze CVs against job details
using the Gemini AI model.
"""

from contextlib import asynccontextmanager
import time
import logging

from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette import status

from app.api.models.models import (
    CVJobAnalysisRequest,
    CoverLetterGeneratorRequest,
    CoverLetterResponse,
    CVJobAnalysisResponse,
)
from app.utils.utils import download_user_cv, generate_and_upload_pdf
from app.utils.ai.gen_ai_utils import (
    format_job_details_for_ai_jobs_analysis,
    format_job_details_for_cover_letter_generation,
    analyze_cv_with_gemini,
    process_gemini_response,
    generate_cover_letter,
    format_cover_letter_response,
)
from app.api.core.core import gemini_client, google_storage_client

# Configure logger
logger = logging.getLogger(__name__)

load_dotenv()


@asynccontextmanager
async def lifespan(application: APIRouter):
    """
    Lifespan context manager for initializing and shutting down the Gemini client.

    This function sets up the Gemini client during the startup phase and
    cleans up resources during the shutdown phase.
    """
    # Startup logic
    application.state.gemini_client = gemini_client
    application.state.google_storage_client = google_storage_client
    logger.info("Gemini client and storage client initialized on gen ai services.")
    yield
    # Shutdown logic
    logger.info("Shutting down gen-ai services resources")


router = APIRouter(
    prefix="/gen-ai-services",
    tags=["gen-ai-services"],
    lifespan=lifespan,
)


@router.post(
    "/cv_job_analysis_flash",
    status_code=status.HTTP_200_OK,
    response_model=CVJobAnalysisResponse,
    responses={
        200: {
            "description": "CV analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "cv_relevance_score": 25,
                        "explaination": [
                            "CV kamu kurang relevan dengan Job Desc karena kamu belum memiliki pengalaman di bidang Data Science.",
                            "Skill teknis yang kamu miliki lebih fokus ke Fullstack Web Development, bukan Data Science.",
                        ],
                        "skill_identification_dict": {
                            "Data Processing": 0,
                            "Python": 0,
                            "Machine Learning Models": 0,
                            # Additional skills omitted for brevity
                        },
                        "suggestions": [
                            {
                                "keypoint": "Pelajari dan perbanyak pengalaman dengan Python dan R",
                                "penjelasan": "Job requirements menyebutkan Python dan R sebagai skill yang dibutuhkan untuk membangun model machine learning.",
                            }
                            # Additional suggestions omitted for brevity
                        ],
                        "processing_time_seconds": 4.14,
                        "model": "gemini-2.5-flash-preview-04-17",
                    }
                }
            },
        },
        500: {"description": "Error analyzing CV"},
    },
)
async def get_cv_job_analysis_flash(
    request: Request, data: CVJobAnalysisRequest = Body(...)
):
    """
    Analyze CV against job details using the Gemini AI model.

    This endpoint analyzes a CV against job requirements to:
    - Calculate a relevance score between the CV and job
    - Identify skill matches and gaps
    - Provide personalized improvement suggestions
    - Highlight strengths and areas for development

    Uses Gemini's flash model for fast, efficient processing.
    """
    start_time = time.time()
    logger.info(
        f"Starting CV analysis for job position: {data.job_details.job_position}"
    )

    try:
        # Get file directly from Google Cloud Storage asynchronously
        logger.info(f"Downloading CV from: {data.cv_url}")
        user_cv_content = await download_user_cv(data.cv_url)
        logger.info(f"Successfully downloaded CV, size: {len(user_cv_content)} bytes")

        # Format job details as formatted text for the model
        formatted_job_details = format_job_details_for_ai_jobs_analysis(
            data.job_details
        )

        # Use the async client for non-blocking requests
        logger.info("Sending CV for analysis with Gemini")
        response = await analyze_cv_with_gemini(
            request.app.state.gemini_client, user_cv_content, formatted_job_details
        )
        logger.info("Received response from Gemini")

        # Process response
        result = process_gemini_response(response.text, time.time() - start_time)
        logger.info(
            f"Analysis complete. CV relevance score: {result.get('cv_relevance_score')}%, time: {result.get('processing_time_seconds')}s"
        )

        return result

    except Exception as e:
        logger.error(f"Error in CV analysis: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)}
        )


@router.post(
    "/cover_letter_generator",
    status_code=status.HTTP_200_OK,
    response_model=CoverLetterResponse,
    responses={
        200: {
            "description": "Cover letter generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "pdf_url": "https://storage.googleapis.com/main-storage-hireon/generated_cv/b5fe7892bca548aa99b6213373674f7c.pdf",
                        "pdf_cloud_path": "generated_cv/b5fe7892bca548aa99b6213373674f7c.pdf",
                        "processing_time_seconds": 70.31,
                        "model": "gemini-2.5-pro-preview-05-06",
                    }
                }
            },
        },
        500: {"description": "Error generating cover letter"},
    },
)
async def cover_letter_generator(
    request: Request, data: CoverLetterGeneratorRequest = Body(...)
):
    """
    Generate a cover letter for a job application.

    This endpoint uses the Gemini AI model to generate a professional cover letter
    based on the user's CV and job details. The cover letter is formatted as a PDF
    and uploaded to Google Cloud Storage.

    Returns a JSON object containing the URL to the generated PDF file and processing metadata.
    """
    start_time = time.time()
    logger.info(
        f"Starting cover letter generation for job: {data.job_details.job_position} at {data.job_details.company_name}"
    )

    try:
        logger.info(f"Downloading CV from: {data.cv_url}")
        user_cv_content = await download_user_cv(data.cv_url)
        logger.info(f"Successfully downloaded CV, size: {len(user_cv_content)} bytes")

        formatted_job_details = format_job_details_for_cover_letter_generation(
            data.job_details
        )

        logger.info("Generating cover letter with Gemini")
        response = await generate_cover_letter(
            request.app.state.gemini_client,
            user_cv_content,
            formatted_job_details,
            data.current_date if hasattr(data, "current_date") else "23 Mei 2025",
            data.spesific_request if hasattr(data, "spesific_request") else None,
        )
        logger.info("Received cover letter from Gemini")

        # Format the response into HTML
        html_content = format_cover_letter_response(response.text)

        # Generate PDF and upload to Cloud Storage
        logger.info("Generating PDF and uploading to Cloud Storage")
        pdf_result = await generate_and_upload_pdf(
            request.app.state.google_storage_client, html_content
        )
        logger.info(f"PDF generated and uploaded: {pdf_result['pdf_url']}")

        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(
            f"Cover letter generation complete, took {processing_time:.2f} seconds"
        )

        return {
            "pdf_url": pdf_result["pdf_url"],
            "pdf_cloud_path": pdf_result["pdf_cloud_path"],
            "processing_time_seconds": round(processing_time, 2),
            "model": "gemini-2.5-pro-preview-05-06",
        }

    except Exception as e:
        logger.error(f"Error in cover letter generation: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)}
        )
