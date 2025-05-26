"""
Module for CV Job Analysis using Gemini AI.

This module provides an API endpoint to analyze CVs against job details
using the Gemini AI model.
"""

from contextlib import asynccontextmanager
import time

from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from google import genai
from google.cloud import storage
from starlette import status

from app.api.models import (
    CVJobAnalysisRequest,
    CoverLetterGeneratorRequest,
    CoverLetterResponse,
    CVJobAnalysisResponse,
)
from app.utils.utils import (
    download_user_cv,
    format_job_details_for_ai_jobs_analysis,
    format_job_details_for_cover_letter_generation,
    analyze_cv_with_gemini,
    process_gemini_response,
    generate_cover_letter,
    format_cover_letter_response,
    generate_and_upload_pdf,
)

load_dotenv()


@asynccontextmanager
async def lifespan(application: APIRouter):
    """
    Lifespan context manager for initializing and shutting down the Gemini client.

    This function sets up the Gemini client during the startup phase and
    cleans up resources during the shutdown phase.
    """
    # Startup logic
    application.state.client = genai.Client()
    application.state.storage_client = storage.Client()
    print("Gemini client and storage client initialized")
    yield
    # Shutdown logic


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
                        "cv_relevance_score": 78,
                        "explaination": [
                            "CV kamu cukup relevan dengan Job Desc, terutama di bagian technical skills dan pengalaman membangun model ML.",
                            "Pengalaman kamu sebagai Founder & Head of AI/ML di startup sangat menarik dan menunjukkan kemampuan end-to-end.",
                            "Ada beberapa area di mana pengalaman kamu bisa diperkuat untuk lebih sesuai dengan kebutuhan spesifik di Job Desc, terutama terkait big data dan beberapa teknologi spesifik.",
                        ],
                        "skill_identification_dict": {
                            "Data Processing and Analysis": 85,
                            "Pattern Discovery": 80,
                            "Insight Gathering": 80,
                            "Predictive Analytics": 90,
                            "Optimization Models": 75,
                            "AI Use Cases Development": 85,
                            "Productivity Enhancement (AI)": 70,
                            "Process Automation (AI)": 70,
                            "New Technology Adoption (AI)": 70,
                            "Cross-functional Collaboration": 80,
                            "Communication of Findings": 75,
                            "Data-driven Solution Implementation": 80,
                            "Continuous Learning (Data Science)": 90,
                            "Stay Updated (Data Science Methods)": 90,
                            "Stay Updated (Data Science Use Cases)": 90,
                            "Stay Updated (Technology Advancements)": 90,
                            "Analytical Skills": 95,
                            "Statistical Skills": 95,
                            "Logical Thinking": 95,
                            "Big Data Analysis": 40,
                            "Data Warehousing": 30,
                            "Business Intelligence": 30,
                            "R": 70,
                            "Python": 90,
                            "Machine Learning Models": 95,
                            "Hadoop": 10,
                            "Spark": 10,
                            "Graph DB": 5,
                            "Gen-AI Use Cases": 70,
                            "Teamwork": 85,
                            "Individual Work": 85,
                        },
                        "suggestions": [
                            {
                                "keypoint": "Perkuat pengalaman dengan teknologi Big Data",
                                "penjelasan": "Job requirements menyebutkan pengalaman dengan big data analysis, data warehousing, dan business intelligence. Di CV kamu belum banyak menyoroti pengalaman di area ini. Coba tambahkan detail proyek atau pengalaman yang relevan, atau pertimbangkan untuk mengambil kursus/sertifikasi terkait dalam 1-3 bulan ke depan.",
                            },
                            {
                                "keypoint": "Highlight pengalaman dengan Hadoop, Spark, dan Graph DB",
                                "penjelasan": "Job requirements menyebutkan pengalaman dengan Hadoop, Spark, dan Graph DB sebagai nilai tambah. Meskipun tidak wajib, memiliki pengalaman ini akan sangat meningkatkan relevansi CV kamu. Jika kamu pernah menggunakan teknologi ini dalam proyek (meskipun kecil), pastikan untuk menyorotnya. Jika belum, pertimbangkan untuk mempelajari dasar-dasarnya dalam 1-2 bulan.",
                            },
                            {
                                "keypoint": "Detailkan kontribusi spesifik dalam proyek AI Use Cases",
                                "penjelasan": "Kamu sudah punya pengalaman bagus dengan AI use cases. Untuk lebih meyakinkan, coba detailkan kontribusi spesifik kamu dalam mengembangkan AI use cases yang bertujuan meningkatkan produktivitas atau mengotomatisasi proses, seperti yang disebutkan di Job Desc. Berikan angka atau metrik jika memungkinkan.",
                            },
                            {
                                "keypoint": "Cantumkan sertifikasi yang paling relevan di bagian awal CV",
                                "penjelasan": "Kamu punya banyak sertifikasi, itu bagus! Untuk Job Desc ini, sertifikasi di bidang Data Analytics, Machine Learning, dan Deep Learning sangat relevan. Coba pindahkan sertifikasi yang paling relevan ke bagian awal CV atau buat bagian 'Relevant Certifications' untuk menyorotnya.",
                            },
                        ],
                        "processing_time_seconds": 5.78,
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

    try:
        # Get file directly from Google Cloud Storage asynchronously
        user_cv_content = await download_user_cv(data.cv_url)

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
        print(f"Error in CV analysis: {str(e)}")
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
                        "pdf_url": "https://storage.googleapis.com/main-storage-hireon/generated_cv/cover_letter_1748024958.pdf",
                        "pdf_cloud_path": "generated_cv/cover_letter_1748024958.pdf",
                        "processing_time_seconds": 54.67,
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

    try:
        user_cv_content = await download_user_cv(data.cv_url)

        formatted_job_details = format_job_details_for_cover_letter_generation(
            data.job_details
        )

        response = await generate_cover_letter(
            request.app.state.client,
            user_cv_content,
            formatted_job_details,
            data.current_date if hasattr(data, "current_date") else "23 Mei 2025",
            data.spesific_request if hasattr(data, "spesific_request") else None,
        )

        # Format the response into HTML
        html_content = format_cover_letter_response(response.text)

        # Generate PDF and upload to Cloud Storage
        pdf_result = await generate_and_upload_pdf(
            request.app.state.storage_client, html_content
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        return {
            "pdf_url": pdf_result["pdf_url"],
            "pdf_cloud_path": pdf_result["pdf_cloud_path"],
            "processing_time_seconds": round(processing_time, 2),
            "model": "gemini-2.5-pro-preview-05-06",
        }

    except Exception as e:
        print(f"Error in cover letter generation: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)}
        )
