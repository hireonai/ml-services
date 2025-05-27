from contextlib import asynccontextmanager

from typing import List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from google.genai import types
import pandas as pd

from app.api.core import create_chroma_client, gemini_client, google_storage_client


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
        print("Successfully loaded existing ChromaDB collections")
    except Exception as e:
        print(f"Error loading collections: {e}")
        print("Collections will be initialized on first use")

    print(
        "Gemini client, google storage client and chroma client initialized on recommendation engine services"
    )
    yield
    # Shutdown logic


class RecommendationsRequest(BaseModel):
    # cv_storage_url: str = Field(..., description="URL to the CV document in storage")
    cv_representation: str = Field(..., description="CV representation")
    search_query: str = Field(
        None, description="Optional search query to filter recommendations"
    )
    filtered_id: List[str] = Field(
        None, description="Optional list of job IDs to filter out"
    )


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


@router.post("/recommendations")
async def recommendations(request: Request, req_data: RecommendationsRequest):
    """Get recommendations for a given user."""

    # Initialize variables
    job_title_results = None

    if req_data.search_query:
        job_title_embedding = (
            request.app.state.gemini_client.models.embed_content(
                model="text-multilingual-embedding-002",
                contents=req_data.search_query,  # Send only one item
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    title="Job Title",
                ),
            )
            .embeddings[0]
            .values
        )

        # Query job_titles collection with the embedding
        job_title_results = await request.app.state.job_titles_collection.query(
            query_embeddings=[job_title_embedding], n_results=10000
        )

    cv_relevance_embedding = (
        request.app.state.gemini_client.models.embed_content(
            model="text-multilingual-embedding-002",
            contents=req_data.cv_representation,  # Use CV representation for embedding
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                title="CV Relevance",
            ),
        )
        .embeddings[0]
        .values
    )

    # Query job descriptions with CV embedding
    job_desc_results = await request.app.state.job_desc_collection.query(
        query_embeddings=[cv_relevance_embedding], n_results=10000
    )

    # Create separate dataframes for each collection
    job_desc_df = pd.DataFrame(
        {
            "id": job_desc_results["ids"][0],
            "job_description": job_desc_results["documents"][0],
            "distance": job_desc_results["distances"][0],
        }
    )

    # Initialize combined dataframe with job descriptions
    combined_df = job_desc_df.copy()

    # Add job title results if they exist
    if job_title_results:
        job_title_df = pd.DataFrame(
            {
                "id": job_title_results["ids"][0],
                "job_title": job_title_results["documents"][0],
                "distance": job_title_results["distances"][0],
            }
        )

        # Merge the dataframes on 'id' column (outer join to keep all entries)
        combined_df = pd.merge(
            job_desc_df,
            job_title_df,
            on="id",
            how="outer",
            suffixes=("__job_desc", "__job_title"),
        )

    # Fill NaN values for any missing distances
    if "title_distance" in combined_df.columns:
        combined_df["title_distance"] = combined_df["title_distance"].fillna(
            float("inf")
        )

    combined_df["hybird_score"] = (
        combined_df["desc_distance__job_title"] * 0.6
        + combined_df["desc_distance__job_desc"] * 0.4
    )
    combined_df["match_score"] = (
        1 - combined_df["hybird_score"] / combined_df["hybird_score"].max()
    )
    combined_df = combined_df.sort_values("match_score", ascending=False)
    combined_df = combined_df[["id", "match_score"]]

    results = {"combined_results": combined_df.to_dict(orient="records")}

    return results
