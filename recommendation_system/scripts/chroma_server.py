from chromadb import HttpClient
from chromadb.config import Settings
import pandas as pd
import logging
from typing import List
from scripts.embedding.gemini_embedding import GeminiEmbeddingFunction



logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])


class ChromaDBHttpClient:
    """
    A class to connect to ChromaDB and perform operations on the database.
    This class provides methods to connect to the database, add texts, query the collection,
    delete the collection, and preview the collection.
    This class uses the GeminiEmbeddingFunction for embedding.
    """

    def __init__(self, collection_name: str, api_key: str, chroma_host: str = "<EXTERNAL_IP>:<PORT>"):
        """
        Initialize ChromaDB client and collection.
        This method sets up the ChromaDB client and creates or gets a collection.

        Args:
            collection_name (str): a string representing the name of the collection.
            api_key (str): API key for Google Generative AI.
            chroma_host (str): Host and port for the ChromaDB server.
        """
        try:
            self.collection_name = collection_name
            self.embedding_function = GeminiEmbeddingFunction(api_key=api_key)

            # setup HTTP client to connect to remote ChromaDB
            self.client = HttpClient(Settings(
                chroma_api_impl="rest",
                chroma_server_host=chroma_host.split(":")[0],
                chroma_server_http_port=int(chroma_host.split(":")[-1]), # make sure again this shoulda int or str
                anonymized_telemetry=False
            ))

            # get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
        except Exception as e:
            logging.error(f"Failed to connect to ChromaDB: {e}")
            raise

    def add_texts(self, ids: List[str], texts: List[str]):
        """
        Add texts to the ChromaDB collection.
        This method takes a list of IDs and a list of texts, and adds them to the collection.
        
        Args:
            ids (List[str]): List of IDs for the texts.
            texts (List[str]): List of texts to be added to the collection.
        
        Raises:
            ValueError: If IDs or texts are not provided or if their lengths do not match.
            Exception: If there is an error adding texts to the collection.
        """
        try:
            if not ids or not texts:
                raise ValueError('IDs and texts must be provided.')
            if len(ids) != len(texts):
                raise ValueError('Length mismatch between IDs and texts.')

            self.collection.add(
                ids=ids,
                documents=texts
            )
            logging.info(f"Added {len(ids)} documents to collection '{self.collection_name}'.")
        except Exception as e:
            logging.error(f'Failed to add texts: {e}')
            raise

    def query(self, query_texts: str, n_results: int = 5) -> pd.DataFrame:
        """
        Query the collection with the provided texts.
        This method takes a list of query texts and returns the top n results.

        Args:
            query_texts (List[str]): List of query texts.
            n_results (int): Number of results to return.
        
        Returns:
            pd.DataFrame: DataFrame containing the IDs and distances of the top results.
        
        Raises:
            ValueError: If query texts are not provided or if n_results is less than or equal to 0.
            Exception: If there is an error querying the collection.
        """
        try:
            if not isinstance(query, list):
                query = [query]
            if query is None:
                raise ValueError('Query is not set.')
            if n_results <= 0:
                raise ValueError('Number of results must be greater than 0.')
            
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results
            )

            ids = results['ids'][0]
            dist = results['distances'][0]

            return pd.DataFrame({
                'id': ids,
                'distance': dist
            })
        except Exception as e:
            logging.error(f'Query failed: {e}')
            raise


    def delete_collection(self):
        """
        Delete the collection from the ChromaDB.
        This method deletes the collection with the specified name.
        
        Raises:
            Exception: If there is an error deleting the collection.
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logging.info(f"Collection '{self.collection_name}' deleted successfully.")
        except Exception as e:
            logging.error(f"Failed to delete collection: {e}")
            raise

    def preview_collection(self):
        """
        Preview the collection.
        This method retrieves a preview of the collection and its count.
        
        Returns:
            tuple: A tuple containing a preview of the collection and its count.
        
        Raises:
            Exception: If there is an error previewing the collection.
        """
        try:
            preview = self.collection.peek()
            count = self.collection.count()
            return preview, count
        except Exception as e:
            logging.error(f'Failed to preview collection: {e}')
            raise

if __name__ == "__main__":
    api_key = "GEMINI_API_KEY"
    chroma_host = "<EXTERNAL IP>:<PORT>"  

    client = ChromaDBHttpClient(collection_name="my_collection", api_key=api_key, chroma_host=chroma_host)

    client.add_texts(ids=["doc1"], texts=["Halo dunia, ini contoh dokumen."])
    results = client.query(["halo dunia"])
    print(results)