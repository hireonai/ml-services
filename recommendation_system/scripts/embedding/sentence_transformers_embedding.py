from sentence_transformers import SentenceTransformer
from chromadb import EmbeddingFunction, Embeddings
from typing import List


class MultilingualEmbeddingFunction(EmbeddingFunction):
    """
    A class to generate multilingual embeddings using an open-source model from Hugging Face.
    This version is CPU-compatible and designed for ChromaDB integration.
    """

    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Initialize the embedding function with the selected multilingual model.
        
        Args:
            model_name (str): The Hugging Face model name. Defaults to 'intfloat/multilingual-e5-small'.
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: List[str]) -> Embeddings:
        """
        Generate embeddings for a list of input texts.
        
        Args:
            input (List[str]): A list containing a single string (or more).
        
        Returns:
            Embeddings: A list of embedding vectors.
        """
        try:
            # special format E5, define: "query: {text}"
            embeddings = self.model.encode(input)
            return embeddings
        except Exception as e:
            raise Exception(f"Error generating embeddings: {e}")


if __name__ == "__main__":
    embed_fn = MultilingualEmbeddingFunction()

    input_text = ["halo dunia"]
    embedding_result = embed_fn(input_text)

    print(embedding_result)
