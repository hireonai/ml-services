import google.generativeai as genai
from google.genai import types
from chromadb import EmbeddingFunction, Embeddings
from typing import List


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    A class to generate embeddings using Google Generative AI's Gemini model.
    This class provides methods to initialize the model and generate embeddings for a list of strings.
    """
    
    def __init__(self, api_key: str, model_name: str = "models/gemini-embedding-exp-03-07"):
        """
        Initialize the GeminiEmbeddingFunction with the provided API key and model name.
        
        Args:
            api_key (str): The API key for Google Generative AI.
            model_name (str): The name of the embedding model to be used. Default is "gemini-embedding-exp-03-07".
        """
        genai.configure(api_key=api_key)
        self.model = genai.Client(api_key=api_key)
        self.model_name = model_name # ["models/embedding-001", "models/text-embedding-004", "models/gemini-embedding-exp-03-07", "models/gemini-embedding-exp"] 


    def __call__(self, input: List[str]) -> Embeddings: 
        """
        Generate embeddings for the provided input texts using the specified model.
        This method takes a list of strings as input and returns the corresponding embeddings.
        
        Args:
            input (list[str]): A list of strings to be embedded.
            
        Returns:
            Embeddings: A list of embeddings corresponding to the input strings.
        
        Raises:
            Exception: If there is an error generating the embeddings.
        """
        title = 'custom query'
        try:
            response = self.model.models.embed_content(
                    model=self.model_name,
                    contents=input,
                    config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",
                    title=title
                    )
                )

            return response.embeddings[0].values.tolist()
        except Exception as e:
            raise Exception(f"Error in embedding: {e}")
        
if __name__ == "__main__":
    api_key = "API_KEY"
    embed_fn = GeminiEmbeddingFunction(api_key=api_key)

    # Input berupa list dengan satu string
    input_text = ["halo dunia"]
    embedding_result = embed_fn(input_text)