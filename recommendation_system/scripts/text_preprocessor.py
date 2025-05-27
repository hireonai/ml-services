import logging
from typing import List
import pandas as pd

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])


class TextPreprocessor:
    """
    A class to prepare data for embedding and load into a chroma database.
    This class provides methods to create ID lists, job title lists, and job texts
    from a DataFrame.
    """
    
    def create_id_list(self, data: pd.DataFrame) -> List[str]:
        """
        Create a list of IDs from the DataFrame.
        The IDs are extracted from the '_id' column and converted to strings.
        The IDs are returned as a list of strings.

        Args:
            data (pd.DataFrame): dataframe containing the data to be processed.

        Returns:
            List[str]: A list of IDs as strings.
        
        Raises:
            ValueError: If the required column is missing in the DataFrame.
            Exception: If there is an error fetching IDs from the DataFrame.
        """
        try:
            if '_id' not in data.columns:
                raise ValueError('Required column is missing in the DataFrame.')
            
            ids_col = '_id'
            ids = data[ids_col].apply(lambda x: str(x))
            return ids.to_list()
        
        except Exception as e:
            logging.error(f'Error fetching IDs: {e}')
            raise
    
    
    def create_job_title_list(self, data: pd.DataFrame) -> List[str]:
        """
        Create a list of job titles from the DataFrame.
        The job titles are extracted from the 'jobPosition' column and returned as a list of strings.

        Args:
            data (pd.DataFrame): dataframe containing the data to be processed.
        
        Returns:
            List[str]: A list of job titles as strings.
        
        Raises:
            ValueError: If the required column is missing in the DataFrame.
            Exception: If there is an error fetching job titles from the DataFrame.
        """
        try:
            if 'jobPosition' not in data.columns:
                raise ValueError('Required column is missing in the DataFrame.')
            
            job_titles_col = 'jobPosition'
            job_titles = data[job_titles_col].to_list()
            return job_titles
        
        except Exception as e:
            logging.error(f'Error fetching job titles: {e}')
            raise
    
    
    def create_job_texts(self, data: pd.DataFrame) -> List[str]:
        """
        Create a list of job texts from the DataFrame.
        The job texts are created by concatenating the 'jobDescList' and 'jobQualificationsList' columns.
        The job descriptions are prefixed with 'Jobdesk: ' and the requirements are prefixed with '. Requirements: '.
        The concatenated job texts are returned as a list of strings.

        Args:
            data (pd.DataFrame): dataframe containing the data to be processed.
        
        Returns:
            List[str]: A list of concatenated job texts as strings.
        
        Raises:
            ValueError: If the required columns are missing in the DataFrame.
            Exception: If there is an error creating job texts from the DataFrame.
        """
        try:
            if 'jobDescList' not in data.columns or 'jobQualificationsList' not in data.columns:
                raise ValueError('Required columns are missing in the DataFrame.')
            
            df = data.copy()
            jobdesk_col = 'jobDescList'
            requirements_col = 'jobQualificationsList'
            concate = df[jobdesk_col].apply(lambda x: 'Jobdesk: ' + ', '.join(x)) + \
                df[requirements_col].apply(lambda x: '. Requirements: ' + ', '.join(x))
            return concate.to_list()
        
        except Exception as e:
            logging.error(f'Error creating job texts: {e}')
            raise
            
            
        