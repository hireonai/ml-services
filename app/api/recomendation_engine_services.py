from contextlib import asynccontextmanager

from fastapi import APIRouter, Request

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
    application.state.chroma_client = await create_chroma_client()
    print(
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


@router.post("/recommendations")
async def recommendations(request: Request):
    """Get recommendations for a given user."""
    return {"status": "ok"}
