from bson import ObjectId
import pandas as pd

class TopSimilarity:
    """
    A class to calculate the similarity between two DataFrames based on their top N records.
    This class provides a method to calculate the weighted similarity between two DataFrames
    and return a list of ObjectId in MongoDB Atlas.
    """
    
    def __init__(self):
        pass

    def weighted_similarity(self,
                            df1: pd.DataFrame,
                            df2: pd.DataFrame,
                            w1: float = 0.7,
                            w2: float = 0.3) -> list[ObjectId]:
        """
        Calculate the weighted similarity between two DataFrames.
        This method takes two DataFrames and calculates the weighted similarity
        based on the top N records from each DataFrame. The method returns a list of ObjectId.

        Args:
            df1 (pd.DataFrame): the first DataFrame containing the first set of records.
            df2 (pd.DataFrame): the second DataFrame containing the second set of records.
            w1 (float): a float representing the weight for the first DataFrame.
            w2 (float): a float representing the weight for the second DataFrame.
        
        Returns:
            list[ObjectId]: a list of ObjectId representing the IDs of the top similar records in MongoDB.
        
        Raises:
            ValueError: If the weights are not between 0 and 1.
            Exception: If there is an error calculating the weighted similarity.
        """
        if not (0 <= w1 <= 1) or not (0 <= w2 <= 1):
            raise ValueError('Weights must be between 0 and 1.')

        if df1.empty or df2.empty:
            raise ValueError('DataFrames cannot be empty.')
        if 'distance' not in df1.columns or 'distance' not in df2.columns:
            raise ValueError("DataFrames must contain a 'distance' column.")
        if 'id' not in df1.columns or 'id' not in df2.columns:
            raise ValueError("DataFrames must contain an 'id' column.")

        # add columns for tracking purposes
        df1 = df1.copy()
        df2 = df2.copy()
        df1['source'] = 'df1'
        df2['source'] = 'df2'

        # combined dataframes, sort by distance, and drop duplicates
        combined_df = pd.concat([df1, df2])
        combined_df = combined_df.sort_values(by='distance', ascending=True)
        combined_df = combined_df.drop_duplicates(subset='id', keep='first')

        # separate the dataframes based on source for apply weights
        from_df1 = combined_df[combined_df['source'] == 'df1']
        from_df2 = combined_df[combined_df['source'] == 'df2']        

        # calculate weights for each dataframe
        total_count = len(combined_df)
        n1 = int(total_count * w1)
        n2 = int(total_count * w2)  

        # take top n1 and n2 records from each dataframe
        top_from_df1 = from_df1.sort_values(by='distance').head(n1)
        top_from_df2 = from_df2.sort_values(by='distance').head(n2)
        
        # concatenate the top records from both dataframes
        final_df = pd.concat([top_from_df1, top_from_df2])
        final_df = final_df.sort_values(by='distance', ascending=True)

        # make the list of ObjectId
        ids = [ObjectId(x) for x in final_df['id'].tolist()]
        
        return ids
