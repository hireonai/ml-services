"""
Recommendation Engine Services module.

This module provides API endpoints for generating job recommendations
based on user CV and search criteria using semantic search and embeddings.
"""

from contextlib import asynccontextmanager
import logging
import time

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi import status

from app.api.models.models import (
    RecommendationsResponse,
    JobRecommendation,
    PostCVEmbeddingsRequest,
)

from app.api.core.core import (
    create_chroma_client,
    google_storage_client,
    gemini_client_vertex_ai,
)
from app.api.core.auth import get_api_key
from app.utils.utils import change_link_storage_to_gs
from app.utils.ai.gen_ai_utils import generate_text_representation_from_cv
from app.utils.recommendation.recommendation_utils import (
    create_embedding,
    query_collection,
    create_dataframe_from_results,
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
        application.state.user_cv_embeddings_collection = (
            await application.state.chroma_client.get_collection(
                name="user_cv_embeddings"
            )
        )
        logger.info("Successfully loaded existing ChromaDB collections")
    except Exception as e:
        logger.error("Error loading collections: %s", e)
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
async def get_status(request: Request, api_key: str = Depends(get_api_key)):
    """Get ChromaDB server status."""
    heartbeat_status = await request.app.state.chroma_client.heartbeat()
    return {"status": heartbeat_status}


@router.get("/cv_embeddings")
async def get_cv_embeddings(
    request: Request, user_id: str, api_key: str = Depends(get_api_key)
):
    """Get CV embeddings for a given user ID."""
    cv_embeddings = await request.app.state.user_cv_embeddings_collection.get(
        ids=user_id, include=["embeddings"]
    )
    return {"embeddings": cv_embeddings["embeddings"][0].tolist()}


@router.post(
    "/cv_embeddings",
    responses={
        200: {
            "description": "Successfully added embedding for user",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "message": "embedding added for user 123",
                        "cv_to_text_response_time": 10.49885368347168,
                        "embedding_creation_time": 1.7401466369628906,
                        "total_response_time": 12.23932147026062,
                    }
                }
            },
        },
        500: {"description": "Error getting CV embeddings"},
    },
)
async def post_cv_embeddings(
    request: Request,
    req_data: PostCVEmbeddingsRequest,
    api_key: str = Depends(get_api_key),
):
    """Get CV embeddings for a given CV URL."""

    start_time = time.time()
    request_id = f"req_{int(start_time)}"
    logger.info(
        "Getting cv embeddings [%s] for CV URL: %s",
        request_id,
        req_data.cv_storage_url,
    )

    try:
        # Get user CV and generate representation
        # Convert CV URL to Google Storage format
        logger.debug("[%s] Converting CV URL to Google Storage format", request_id)
        try:
            gs_link = await change_link_storage_to_gs(req_data.cv_storage_url)
            logger.debug("[%s] Successfully converted CV URL to GS format", request_id)
        except Exception as e:
            logger.error(
                "[%s] Failed to convert CV URL to Google Storage format: %s",
                request_id,
                str(e),
                exc_info=True,
            )
            raise

        # Measure CV to text conversion time
        cv_to_text_start_time = time.time()
        user_cv_representation = await generate_text_representation_from_cv(
            request.app.state.gemini_client_vertex_ai, gs_link
        )
        cv_to_text_response_time = time.time() - cv_to_text_start_time
        logger.info(
            "[%s] CV to text conversion completed in %.2f seconds",
            request_id,
            cv_to_text_response_time,
        )

        # Generate embedding for CV - measure time separately
        logger.info("[%s] Creating embedding from CV content", request_id)
        embedding_start_time = time.time()
        cv_embedding = await create_embedding(
            request.app.state.gemini_client_vertex_ai, user_cv_representation.text
        )
        embedding_creation_time = time.time() - embedding_start_time
        logger.info(
            "[%s] Embedding creation completed in %.2f seconds",
            request_id,
            embedding_creation_time,
        )

        total_response_time = time.time() - start_time
        logger.info(
            "[%s] Total CV embeddings processing completed in %.2f seconds",
            request_id,
            total_response_time,
        )

        await request.app.state.user_cv_embeddings_collection.upsert(
            embeddings=[cv_embedding], ids=[req_data.user_id]
        )

        return {
            "status": 200,
            "message": f"embedding added for user {req_data.user_id}",
            "cv_to_text_response_time": cv_to_text_response_time,
            "embedding_creation_time": embedding_creation_time,
            "total_response_time": total_response_time,
        }
    except Exception as e:
        logger.error(
            "[%s] Error getting CV embeddings: %s", request_id, str(e), exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "request_id": request_id},
        )


@router.get(
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
                        ],
                        "metrics": {
                            "chroma_query_response_time": 0.32,
                            "total_response_time": 3.21,
                        },
                    }
                }
            },
        },
        500: {"description": "Error generating recommendations"},
    },
)
async def get_recommendations(
    request: Request, user_id: str, api_key: str = Depends(get_api_key)
):
    """Get recommendations for a given user based on their CV."""

    start_time = time.time()
    request_id = f"req_{int(start_time)}"
    logger.info(
        "Starting recommendation generation [%s] for User ID: %s",
        request_id,
        user_id,
    )

    try:
        cv_embedding = await request.app.state.user_cv_embeddings_collection.get(
            ids=user_id, include=["embeddings"]
        )
        cv_embedding = cv_embedding["embeddings"][0]

        # Query job descriptions with CV embedding
        logger.info("[%s] Querying job descriptions based on CV", request_id)
        chroma_query_start_time = time.time()
        job_desc_results = await query_collection(
            request.app.state.job_desc_collection, cv_embedding
        )
        chroma_query_response_time = time.time() - chroma_query_start_time
        logger.info(
            "[%s] ChromaDB query completed in %.2f seconds",
            request_id,
            chroma_query_response_time,
        )

        # Create dataframe from results
        logger.debug("[%s] Processing query results into dataframe", request_id)
        job_desc_df = create_dataframe_from_results(job_desc_results, "job_description")

        job_desc_df["match_score"] = (
            1
            - job_desc_df["job_description_distance"]
            / job_desc_df["job_description_distance"].max()
        ) * 100

        combined_df = job_desc_df[["id", "match_score"]].sort_values(
            "match_score", ascending=False
        )

        # Format the response to match the RecommendationsResponse model
        logger.info(
            "[%s] Preparing response with %d recommendations",
            request_id,
            len(combined_df),
        )
        recommendations_list = []
        for item in combined_df.to_dict(orient="records"):
            recommendations_list.append(
                JobRecommendation(
                    job_id=item["id"], similarity_score=float(item["match_score"])
                )
            )

        total_response_time = time.time() - start_time
        logger.info(
            "[%s] Total recommendation processing completed in %.2f seconds",
            request_id,
            total_response_time,
        )

        return {
            "recommendations": recommendations_list,
            "metrics": {
                "chroma_query_response_time": chroma_query_response_time,
                "total_response_time": total_response_time,
            },
        }

    except Exception as e:
        logger.error(
            "[%s] Error generating recommendations: %s",
            request_id,
            str(e),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "request_id": request_id},
        )
