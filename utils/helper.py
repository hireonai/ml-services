import requests
from io import BytesIO

def download_from_gcs_url(url):
    """Download file from Google Cloud Storage URL and store as binary data in memory.
    
    Args:
        url (str): Public or signed URL to the GCS object
        
    Returns:
        bytes: Binary content of the downloaded file
    """
    # Send HTTP GET request to the URL
    response = requests.get(url)
    
    # Check if request was successful
    response.raise_for_status()
    
    # Get binary content
    binary_content = response.content
    
    return binary_content