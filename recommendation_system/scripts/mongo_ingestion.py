from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.collection import Collection
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])


class MongoDBClient:
    """
    A class to connect to MongoDB Atlas and perform operations on the database.
    This class provides methods to connect to the database, get collections, find documents,
    and close the connection.
    """
    
    def __init__(self, mongo_uri: str, dbname: str):
        """
        Initialize mongoDB Atlas uri and database name.
        This method sets up the MongoDB client and connects to the database.
        
        Args:
            mongo_uri (str): a string representing the MongoDB Atlas URI.
            dbname (str): a string representing the name of the database.
            
        Raises:
            ValueError: If the MongoDB URI or database name is not set.
            Exception: If there is an error inputting the MongoDB URI or database name.
        """
        
        try:
            if mongo_uri is None:
                raise ValueError('MongoDB URI is not set.')
            if dbname is None:
                raise ValueError('Database name is not set.')
            
            self.mongo_uri = mongo_uri
            self.dbname = dbname
            self.mongodb_client = MongoClient(self.mongo_uri,
                                              server_api=ServerApi(
                                                  version='1',
                                                  strict=True,
                                                  deprecation_errors=True
                                            ))
            self.database = self.mongodb_client[self.dbname]

        except Exception as e:
            logging.error(f'Error connecting to MongoDB Atlas: {e}')
            raise
        
    def __enter__(self):
        """
        Enter the runtime context related to this object.
        
        Returns:
            MongoDBClient: The MongoDB client instance.
        """
        try:
            if self.mongodb_client is None:
                raise ValueError('MongoDB client is not initialized.')
            
            return self
        except Exception as e:
            logging.error(f'Error entering MongoDB context: {e}')
            raise
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the runtime context related to this object.
        
        Args:
            exc_type: The exception type.
            exc_value: The exception value.
            traceback: The traceback object.
        
        Raises:
            Exception: If there is an error closing the MongoDB Atlas connection.
        """
        if self.mongodb_client:
            self.mongodb_client.close()
            
    def ping(self):
        """
        Ping the MongoDB Atlas server to check if the connection is successful.
        
        Raises:
            Exception: If the ping fails.
        """
        try:
            if self.mongodb_client is None:
                raise ValueError('MongoDB client is not initialized.')
            
            self.mongodb_client.admin.command('ping')
            logging.info('MongoDB Atlas ping successfully.')
            return True
        except Exception as e:
            logging.error(f'Error pinging MongoDB Atlas: {e}')
            raise

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.
        This method takes a collection name and returns the corresponding collection object.

        Args:
            collection_name (str): a string representing the name of the collection in the database.

        Returns:
            collection: a MongoDB collection object.
            
        Raises:
            ValueError: If the collection name is not set.
            Exception: If there is an error getting the collection.
        """
        try:
            if collection_name is None:
                raise ValueError('Collection name is not set.')
            
            collection = self.database[collection_name]
            return collection
        
        except Exception as e:
            logging.error(f'Error getting collection {collection_name}: {e}')
            raise

    def find(self, collection_name, filter={}, projection=None, limit=0) -> list[dict]:
        """
        Find documents in a MongoDB collection.
        
        Args:
            collection_name (str): a string representing the name of the collection in the database.
            filter (dict): a dictionary representing the filter to apply to the query.
            projection (dict): a dictionary representing the fields to include or exclude in the result.
            limit (int): an integer representing the maximum number of documents to return.
            
        Returns:
            items (list): a list of dictionaries representing the documents found in the collection.
        
        Raises:
            ValueError: If the collection name is not set.
            Exception: If there is an error finding documents in the collection.
        """
        try:
            if collection_name is None:
                raise ValueError('Collection name is not set.')
            
            collection = self.database[collection_name]
            items = list(collection.find(filter=filter, projection=projection, limit=limit))
            return items
        
        except Exception as e:
            logging.error(f'Error finding documents in collection {collection_name}: {e}')
            raise
                
    def close(self):
        """
        Close the MongoDB Atlas connection.
        
        Raises:
            Exception: If there is an error closing the MongoDB Atlas connection.
        """
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
                logging.info('MongoDB Atlas connection closed.')
                
        except Exception as e:
            logging.error(f'Error closing MongoDB Atlas connection: {e}')
            raise