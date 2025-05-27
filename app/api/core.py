import os

import chromadb
from google import genai
from google.cloud import storage

from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
google_storage_client = storage.Client()


# Async factory function for ChromaDB client
async def create_chroma_client():
    """Create and initialize async ChromaDB client."""
    client = await chromadb.AsyncHttpClient(
        host=os.getenv("CHROMA_SERVER_HOST"),
        port=8000,
    )
    return client
