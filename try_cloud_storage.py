
import os
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_CLOUD_STORAGE_SERVICE_ACCOUNT_PATH")

storage_client = storage.Client()

