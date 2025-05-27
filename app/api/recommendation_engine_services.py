"""
Recommendation Engine Services module.

This module provides API endpoints for generating job recommendations
based on user CV and search criteria using semantic search and embeddings.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import status

from app.api.models import (
    RecommendationsRequest,
    RecommendationsResponse,
    JobRecommendation,
)

from app.api.core import (
    create_chroma_client,
    gemini_client,
    google_storage_client,
    gemini_client_vertex_ai,
)
from app.utils.utils import download_user_cv
from app.utils.gen_ai_utils import generate_text_representation_from_cv
from app.utils.recommendation_utils import (
    create_embedding,
    query_collection,
    create_dataframe_from_results,
    merge_dataframes,
)

# Configure logger
logger = logging.getLogger(__name__)


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

    # Initialize ChromaDB client
    application.state.chroma_client = await create_chroma_client()

    # Get or create collections
    try:
        application.state.job_titles_collection = (
            await application.state.chroma_client.get_collection(
                name="job_titles_documents"
            )
        )
        application.state.job_desc_collection = (
            await application.state.chroma_client.get_collection(
                name="job_desc_req_documents"
            )
        )
        logger.info("Successfully loaded existing ChromaDB collections")
    except Exception as e:
        logger.error(f"Error loading collections: {e}")
        logger.info("Collections will be initialized on first use")

    logger.info(
        "Gemini client, google storage client and chroma client initialized on recommendation engine services"
    )
    yield
    # Shutdown logic


router = APIRouter(
    prefix="/recommendation-engine",
    tags=["recommendation-engine"],
    lifespan=lifespan,
)


@router.get("/status")
async def status(request: Request):
    """Get ChromaDB server status."""
    heartbeat_status = await request.app.state.chroma_client.heartbeat()
    return {"status": heartbeat_status}


@router.post(
    "/recommendations",
    response_model=RecommendationsResponse,
    responses={
        200: {
            "description": "Recommendations generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "recommendations": [
                            {
                                "job_id": "68341f06d64eecb3953d5c3b",
                                "similarity_score": 0.85,
                            },
                            {
                                "job_id": "68341f06d64eecb3953d5adc",
                                "similarity_score": 0.72,
                            },
                        ]
                    }
                }
            },
        },
        500: {"description": "Error generating recommendations"},
    },
)
async def recommendations(request: Request, req_data: RecommendationsRequest):
    """Get recommendations for a given user."""
    try:
        # Get user CV and generate representation
        user_cv = await download_user_cv(req_data.cv_storage_url)
        user_cv_representation = await generate_text_representation_from_cv(
            request.app.state.gemini_client, user_cv
        )

        # Process search query if provided
        job_title_results = None
        if req_data.search_query:
            # Generate embedding for job title search
            job_title_embedding = await create_embedding(
                request.app.state.gemini_client_vertex_ai, req_data.search_query
            )

            # Query job titles collection
            job_title_results = await query_collection(
                request.app.state.job_titles_collection, job_title_embedding
            )

        # Generate embedding for CV
        cv_embedding = await create_embedding(
            request.app.state.gemini_client_vertex_ai, user_cv_representation.text
        )

        # Query job descriptions with CV embedding
        job_desc_results = await query_collection(
            request.app.state.job_desc_collection, cv_embedding
        )

        # Create dataframes from results
        job_desc_df = create_dataframe_from_results(job_desc_results, "job_description")

        # Process job title results if they exist
        job_title_df = None
        if job_title_results:
            job_title_df = create_dataframe_from_results(job_title_results, "job_title")

        # Merge results and calculate scores
        combined_df = merge_dataframes(job_desc_df, job_title_df)

        # Format the response to match the RecommendationsResponse model
        recommendations_list = []
        for item in combined_df.to_dict(orient="records"):
            recommendations_list.append(
                JobRecommendation(
                    job_id=item["id"], similarity_score=float(item["match_score"])
                )
            )

        return {"recommendations": recommendations_list}

    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": str(e)}
        )
