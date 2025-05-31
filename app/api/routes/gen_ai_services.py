"""
Module for CV Job Analysis using Gemini AI.

This module provides an API endpoint to analyze CVs against job details
using the Gemini AI model.
"""

from contextlib import asynccontextmanager
import time
import logging

from fastapi import APIRouter, Request, Body, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette import status

from app.api.models.models import (
    CVJobAnalysisRequest,
    CoverLetterGeneratorRequest,
    CoverLetterResponse,
    CVJobAnalysisResponse,
    GeneralCVAnalysisResponse,
)
from app.utils.utils import (
    generate_and_upload_pdf,
    change_link_storage_to_gs,
)
from app.utils.ai.gen_ai_utils import (
    format_job_details_for_ai_jobs_analysis,
    format_job_details_for_cover_letter_generation,
    analyze_cv_with_gemini,
    process_gemini_response,
    generate_cover_letter,
    format_cover_letter_response,
    general_cv_analysis,
)
from app.api.core.core import (
    gemini_client,
    gemini_client_vertex_ai,
    google_storage_client,
)
from app.api.core.auth import get_api_key

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
    application.state.gemini_client_vertex_ai = gemini_client_vertex_ai
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
                        "cv_relevance_score": 18,
                        "skill_identification_dict": {
                            "Data processing and analysis": 20,
                            "Pattern discovery and insights gathering": 20,
                            "Predictive analytics": 0,
                            "Python": 0,
                            "Machine learning models": 0,
                            "Analytical skills": 40,
                            "Statistical skills": 0,
                            "Logical thinking": 90,
                            "Communication": 70,
                            "Database design": 60,
                        },
                        "areas_for_improvement": [
                            "Lack of specific Data Science technical skills (R, Python, Machine Learning, Big Data tools).",
                            "Experience is primarily in Fullstack Web Development, not Data Science.",
                            "No mention of projects or experience related to predictive analytics or AI.",
                        ],
                        "analysis_explanation": "Your CV currently presents a strong profile in Fullstack Web Development, showcasing expertise in various web technologies, project management, and teamwork. However, for a Data Scientist role, there's a significant mismatch in core technical skills and experience.",
                        "suggestions": [
                            "Create a dedicated 'Data Science Projects' section to showcase any personal projects using R or Python for data analysis.",
                            "Enroll in online courses or certifications for Python/R for Data Science, Machine Learning, and Statistical Modeling.",
                        ],
                        "processing_time_seconds": 23.85,
                        "model": "gemini-2.5-flash-preview-05-20",
                    }
                }
            },
        },
        500: {"description": "Error analyzing CV"},
    },
)
async def get_cv_job_analysis_flash(
    request: Request,
    data: CVJobAnalysisRequest = Body(...),
    api_key: str = Depends(get_api_key),
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
        "Starting CV analysis for job position: %s", data.job_details.job_position
    )

    try:
        # Convert CV URL to Google Storage format
        logger.info("Converting CV URL to Google Storage format: %s", data.cv_url)
        gs_link = await change_link_storage_to_gs(data.cv_url)
        logger.info("Successfully converted CV URL to GS format")

        # Format job details as formatted text for the model
        formatted_job_details = format_job_details_for_ai_jobs_analysis(
            data.job_details
        )

        # Use the async client for non-blocking requests
        logger.info("Sending CV for analysis with Gemini")
        response = await analyze_cv_with_gemini(
            request.app.state.gemini_client_vertex_ai, gs_link, formatted_job_details
        )
        logger.info("Received response from Gemini")

        # Process response
        result = process_gemini_response(response.text, time.time() - start_time)
        logger.info(
            "Analysis complete. CV relevance score: %d%%, time: %ss",
            result.get("cv_relevance_score"),
            result.get("processing_time_seconds"),
        )

        return result

    except Exception as e:
        logger.error("Error in CV analysis: %s", str(e), exc_info=True)
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
    request: Request,
    data: CoverLetterGeneratorRequest = Body(...),
    api_key: str = Depends(get_api_key),
):
    """
    Generate a cover letter for a job application.

    This endpoint uses the Gemini AI model to generate a professional cover letter
    based on the user's CV and job details. The cover letter is formatted as a PDF
    and uploaded to Google Cloud Storage.

    Returns a JSON object containing the URL to the generated PDF file and processing metadata.
    """
    start_time = time.time()
    request_id = f"req_{int(start_time)}"
    logger.info(
        "Starting cover letter generation [%s] for job: %s at %s",
        request_id,
        data.job_details.job_position,
        data.job_details.company_name,
    )

    try:
        # Convert CV URL to Google Storage format
        logger.debug("[%s] Converting CV URL to Google Storage format", request_id)
        try:
            gs_link = await change_link_storage_to_gs(data.cv_url)
            logger.debug("[%s] Successfully converted CV URL to GS format", request_id)
        except Exception as e:
            logger.error(
                "[%s] Failed to convert CV URL to Google Storage format: %s",
                request_id,
                str(e),
                exc_info=True,
            )
            raise

        # Format job details for AI processing
        logger.debug(
            "[%s] Formatting job details for cover letter generation", request_id
        )
        formatted_job_details = format_job_details_for_cover_letter_generation(
            data.job_details
        )

        # Generate cover letter with Gemini
        gen_start_time = time.time()
        logger.info(
            "[%s] Sending request to Gemini for cover letter generation", request_id
        )

        current_date = (
            data.current_date
            if hasattr(data, "current_date") and data.current_date
            else "None, dont use date."
        )

        specific_request = (
            data.spesific_request if hasattr(data, "spesific_request") else None
        )

        try:
            response = await generate_cover_letter(
                request.app.state.gemini_client_vertex_ai,
                gs_link,
                formatted_job_details,
                current_date,
                specific_request,
            )
            gen_time = time.time() - gen_start_time
            logger.info(
                "[%s] Received cover letter from Gemini (%.2f seconds)",
                request_id,
                gen_time,
            )
        except Exception as e:
            logger.error(
                "[%s] Error while generating cover letter with Gemini: %s",
                request_id,
                str(e),
                exc_info=True,
            )
            raise

        # Format response into HTML
        logger.debug("[%s] Formatting cover letter response to HTML", request_id)
        html_content = format_cover_letter_response(response.text)

        # Generate PDF and upload to Cloud Storage
        pdf_start_time = time.time()
        logger.info("[%s] Generating PDF and uploading to Cloud Storage", request_id)
        try:
            pdf_result = await generate_and_upload_pdf(
                request.app.state.google_storage_client, html_content
            )
            pdf_time = time.time() - pdf_start_time
            logger.info(
                "[%s] PDF generated and uploaded successfully: %s (%.2f seconds)",
                request_id,
                pdf_result["pdf_url"],
                pdf_time,
            )
        except Exception as e:
            logger.error(
                "[%s] Error generating or uploading PDF: %s",
                request_id,
                str(e),
                exc_info=True,
            )
            raise

        # Calculate processing time and prepare response
        processing_time = time.time() - start_time
        logger.info(
            "[%s] Cover letter generation complete, took %.2f seconds",
            request_id,
            processing_time,
        )

        return {
            "pdf_url": pdf_result["pdf_url"],
            "pdf_cloud_path": pdf_result["pdf_cloud_path"],
            "processing_time_seconds": round(processing_time, 2),
            "model": "gemini-2.5-flash-preview-05-20",
        }

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            "[%s] Error in cover letter generation (%.2f seconds): %s",
            request_id,
            total_time,
            str(e),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "request_id": request_id},
        )


@router.post(
    "/general-cv-analysis",
    status_code=status.HTTP_200_OK,
    response_model=GeneralCVAnalysisResponse,
    responses={
        200: {
            "description": "CV analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "overall_score": 92,
                        "score_breakdown": {
                            "technical_skills": 95,
                            "experience_relevance": 95,
                            "education": 90,
                            "achievement": 90,
                        },
                        "cv_strengths": [
                            "Demonstrated strong leadership and product development experience",
                            "Extensive technical expertise in AI/ML and Computer Vision",
                        ],
                        "areas_for_improvement": [
                            "Consider categorizing the 'SKILLS' section for improved readability"
                        ],
                        "section_analysis": {
                            "work_experience": {
                                "score": 95,
                                "comment": "Strong work experience section showing leadership",
                            },
                            "education": {
                                "score": 90,
                                "comment": "Solid educational background",
                            },
                            "skills": {
                                "score": 95,
                                "comment": "Comprehensive technical skills",
                            },
                            "achievements": {
                                "score": 90,
                                "comment": "Rich with quantifiable achievements",
                            },
                        },
                        "processing_time_seconds": 19.89,
                        "model": "gemini-2.5-flash-preview-05-20",
                    }
                }
            },
        },
        500: {"description": "Error analyzing CV"},
    },
)
async def get_general_cv_analysis(
    request: Request,
    cv_file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
):
    """
    Analyze a CV and provide a general analysis.

    This endpoint accepts a CV file upload and analyzes it using the Gemini AI model
    to provide a general assessment of strengths, weaknesses, and improvement areas.
    """
    start_time = time.time()
    request_id = f"req_{int(start_time)}"
    logger.info(
        "[%s] Starting general CV analysis for uploaded file: %s",
        request_id,
        cv_file.filename,
    )

    try:
        # Process uploaded file
        logger.debug("[%s] Reading CV file content", request_id)
        cv_content = await cv_file.read()

        # Call Gemini for analysis
        logger.info("[%s] Sending CV to Gemini for analysis", request_id)
        gen_start_time = time.time()
        response = await general_cv_analysis(
            request.app.state.gemini_client_vertex_ai,
            cv_content,
        )
        gen_time = time.time() - gen_start_time
        logger.info(
            "[%s] Received response from Gemini (%.2f seconds)", request_id, gen_time
        )

        # Process the response
        logger.debug("[%s] Processing Gemini response", request_id)
        result = process_gemini_response(response.text, time.time() - start_time)

        # Log results
        processing_time = time.time() - start_time
        logger.info(
            "[%s] CV analysis complete, overall score: %d, took %.2f seconds",
            request_id,
            result.get("overall_score", 0),
            processing_time,
        )

        return result

    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            "[%s] Error in general CV analysis (%.2f seconds): %s",
            request_id,
            total_time,
            str(e),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "request_id": request_id},
        )
