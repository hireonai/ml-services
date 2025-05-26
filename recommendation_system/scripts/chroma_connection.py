from .embedding.sentence_transformers_embedding import MultilingualEmbeddingFunction
from chromadb.config import Settings
from chromadb import Client
import logging
from typing import List
import pandas as pd

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

class ChromaDBClient:
    """
    A class to connect to ChromaDB and perform operations on the database.
    This class provides methods to connect to the database, add texts, query the collection,
    delete the collection, and preview the collection.
    This class uses the SentenceTransformerEmbeddingFunction for embedding.
    """
    
    def __init__(self, collection_name: str):
        """
        Initialize ChromaDB client and collection.
        This method sets up the ChromaDB client and creates or gets a collection.
        It also sets up the embedding function to be used for the collection.
        
        Args:
            collection_name (str): a string representing the name of the collection.
            embedding_model (str): a string representing the embedding model to be used.
        
        Raises:
            ValueError: If the collection name or embedding model is not set.
            Exception: If there is an error connecting to ChromaDB.
        """
        try:
            if collection_name is None:
                raise ValueError('collection is not set.')
            
            self.collection_name = collection_name
            
            # setup embedding function
            self.embedding_function = MultilingualEmbeddingFunction()
            
            # setup ChromaDB client
            self.client = Client(Settings(
                        anonymized_telemetry=False
                    ))

            # create or get collection
            self.collection = self.client.get_or_create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function
                    )
        except Exception as e:
            logging.error(f'Error connecting to Chroma: {e}')
            raise

    def add_texts(self, ids: List[str], texts: list[str]):
        """
        Add texts to the ChromaDB collection.
        This method takes a list of IDs and a list of texts, and adds them to the collection.
        
        Args:
            ids (list[str]): a list of IDs to be added to the collection.
            texts (list[str]): a list of texts to be added to the collection.
        
        Raises:
            ValueError: If the IDs or texts are not set, or if their lengths do not match.
            Exception: If there is an error adding texts to the collection.
        """
        
        try:
            if ids is None or texts is None:
                raise ValueError('IDs or texts are not set.')
            
            if len(ids) != len(texts):
                raise ValueError('Length of IDs and texts do not match.')
            
            self.collection.add(
                ids=ids,
                documents=texts
            )
        except Exception as e:
            logging.error(f'Error adding texts to Chroma: {e}')
            raise
    
    def query(self, query: str, n_results: int = 5) -> pd.DataFrame:
        """
        Query the ChromaDB collection.
        This method takes a query string and returns the top n results from the collection.
        
        Args:
            query (list[str]): a list of query strings to be used for querying the collection.
            n_results (int): an integer representing the number of results to return.
            
        Returns:
            pd.DataFrame: a DataFrame containing the IDs, documents, and distances of the results.
        
        Raises:
            ValueError: If the query is not set or if the number of results is less than or equal to 0.
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
                query_texts=query,
                n_results=n_results
            )
            
            ids = results['ids'][0]
            dist = results['distances'][0]
            docs = results['documents'][0]
            return pd.DataFrame({
                'id': ids,
                'document': docs,
                'distance': dist
            })
        except Exception as e:
            logging.error(f'Error querying Chroma: {e}')
            raise
    
    def delete_collection(self):
        """
        Delete the ChromaDB collection.
        This method deletes the collection from the ChromaDB client.
        
        Raises:
            Exception: If there is an error deleting the collection.
        """
        try:
            self.client.delete_collection(self.collection_name)
            logging.info(f'Collection {self.collection_name} deleted successfully.')
        except Exception as e:
            logging.error(f'Error deleting collection {self.collection_name}: {e}')
            raise
    
    def preview_collection(self):
        """
        Preview the ChromaDB collection.
        This method returns a preview of the collection and the number of documents in it.
        
        Returns:
            first ten documents in the collection and the number of documents.
        
        Raises:
            Exception: If there is an error previewing the collection.
        """
        try:
            return self.collection.peek(), self.collection.count()
        except Exception as e:
            logging.error(f'Error previewing collection {self.collection_name}: {e}')
            raise