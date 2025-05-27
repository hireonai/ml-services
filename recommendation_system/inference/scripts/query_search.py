import pandas as pd
import chromadb


class ChromaQueryClient:
    """
    A class to query ChromaDB collections using a shared embedding function.
    """

    def __init__(self, host: str = '<EXTERNAL IP>', port: int = 8000):
        self.client = chromadb.HttpClient(host=host, port=port)

    def _query(self,
               collection_name: str,
               input_text: str,
               n_results: int = 5) -> pd.DataFrame:
        """
        Query a specific ChromaDB collection with input text and return results as a DataFrame.

        Args:
            collection_name (str): Name of the ChromaDB collection.
            input_text (str): Text to be queried.
            n_results (int): Number of top results to return.

        Returns:
            pd.DataFrame: DataFrame containing 'id' and 'distance' of the results.
        """
        collection = self.client.get_collection(collection_name)
        results = collection.query(query_texts=[input_text], n_results=n_results)

        data = {
            "id": results["ids"][0],
            "distance": results["distances"][0]
        }
        return pd.DataFrame(data)
    
    def query_job_titles(self, job_title: str, n_results: int = 5) -> pd.DataFrame:
        """
        Query the job_titles collection based on job title input.
        """
        return self._query("job_titles", [job_title], n_results)

    def query_job_descriptions(self, job_description: str, n_results: int = 5) -> pd.DataFrame:
        """
        Query the job_descriptions collection based on job description input.
        """
        return self._query("job_descriptions", [job_description], n_results)

    def query_resumes(self, resume_text: str, n_results: int = 5) -> pd.DataFrame:
        """
        Query the resumes collection based on resume text input.
        """
        return self._query("job_descriptions", [resume_text], n_results)
    

