from typing import List, Dict, Any, Optional

from google.genai import types
import pandas as pd


async def create_embedding(client, content: str, task_type: str = "RETRIEVAL_QUERY"):
    """Generate embedding for the given content."""
    embedding = (
        client.models.embed_content(
            model="text-multilingual-embedding-002",
            contents=content,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        .embeddings[0]
        .values
    )

    return embedding


async def query_collection(collection, embedding: List[float], n_results: int = 10000):
    """Query a collection with the given embedding."""
    results = await collection.query(query_embeddings=[embedding], n_results=n_results)
    return results


def create_dataframe_from_results(results: Dict[str, Any], source_type: str):
    """Create a dataframe from query results."""
    return pd.DataFrame(
        {
            "id": results["ids"][0],
            f"{source_type}": results["documents"][0],
            f"{source_type}_distance": results["distances"][0],
        }
    )


def merge_dataframes(
    job_desc_df: pd.DataFrame, job_title_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Merge job description and job title dataframes if available."""
    if job_title_df is None:
        job_desc_df = job_desc_df.rename(
            columns={"job_description_distance": "match_score"}
        )
        combined_df = job_desc_df[["id", "match_score"]]
        return combined_df.sort_values("match_score", ascending=False)

    # Merge the dataframes on 'id' column
    combined_df = pd.merge(
        job_desc_df, job_title_df, on="id", how="outer", suffixes=("_desc", "_title")
    )

    # Calculate hybrid score (60% title, 40% description)
    combined_df["hybrid_score"] = (
        combined_df["job_title_distance"] * 0.6
        + combined_df["job_description_distance"] * 0.4
    )

    # Calculate match score (normalized)
    combined_df["match_score"] = (
        1 - combined_df["hybrid_score"] / combined_df["hybrid_score"].max()
    )

    # Select and sort results
    combined_df = combined_df[["id", "match_score"]]
    return combined_df.sort_values("match_score", ascending=False)
