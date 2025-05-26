from dotenv import load_dotenv
from os import getenv

# load environment variables from .env file
load_dotenv()

# take the variables
MONGO_URI = getenv('MONGO_URI')
DB_NAME = getenv('DB_NAME')
GEMINI_API_KEY = getenv('GEMINI_API_KEY')
