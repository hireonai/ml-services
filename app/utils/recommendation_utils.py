from typing import List, Dict, Any, Optional
import logging

from google.genai import types
import pandas as pd

# Configure logger
logger = logging.getLogger(__name__)


async def create_embedding(client, content: str, task_type: str = "RETRIEVAL_QUERY"):
    """Generate embedding for the given content."""
    logger.info(f"Creating embedding with task type: {task_type}")

    embedding = (
        client.models.embed_content(
            model="text-multilingual-embedding-002",
            contents=content,
            config=types.EmbedContentConfig(task_type=task_type),
        )
        .embeddings[0]
        .values
    )

    logger.info(f"Embedding created successfully, dimension: {len(embedding)}")
    return embedding


async def query_collection(collection, embedding: List[float], n_results: int = 10000):
    """Query a collection with the given embedding."""
    logger.info(f"Querying collection '{collection.name}' for {n_results} results")

    results = await collection.query(query_embeddings=[embedding], n_results=n_results)

    logger.info(f"Query completed, found {len(results['ids'][0])} matches")
    return results


def create_dataframe_from_results(results: Dict[str, Any], source_type: str):
    """Create a dataframe from query results."""
    logger.info(f"Creating dataframe from {source_type} results")

    df = pd.DataFrame(
        {
            "id": results["ids"][0],
            f"{source_type}": results["documents"][0],
            f"{source_type}_distance": results["distances"][0],
        }
    )

    logger.info(f"Dataframe created with {len(df)} rows")
    return df


def merge_dataframes(
    job_desc_df: pd.DataFrame, job_title_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Merge job description and job title dataframes if available."""
    if job_title_df is None:
        logger.info("No job title results, using only job description for scoring")

        job_desc_df = job_desc_df.rename(
            columns={"job_description_distance": "match_score"}
        )
        combined_df = job_desc_df[["id", "match_score"]]

        logger.info(f"Created result dataframe with {len(combined_df)} rows")
        return combined_df.sort_values("match_score", ascending=False)

    # Merge the dataframes on 'id' column
    logger.info("Merging job description and job title dataframes")

    combined_df = pd.merge(
        job_desc_df, job_title_df, on="id", how="outer", suffixes=("_desc", "_title")
    )

    logger.info(f"Merged dataframe created with {len(combined_df)} rows")

    # Calculate hybrid score (60% title, 40% description)
    logger.info("Calculating hybrid scores (60% title, 40% description)")
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
    logger.info(f"Final result dataframe created with {len(combined_df)} rows")

    return combined_df.sort_values("match_score", ascending=False)
