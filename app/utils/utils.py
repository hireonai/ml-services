"""
General utility functions for the application.

This module provides helper functions shared across different services.
"""

import asyncio
import io
import uuid
import aiohttp
import logging

from weasyprint import HTML

# Configure logger
logger = logging.getLogger(__name__)


async def download_user_cv(cv_url: str) -> bytes:
    """
    Download a CV file from a public URL.

    Args:
        cv_url: Public URL to the CV file

    Returns:
        bytes: The CV file content as bytes
    """
    logger.info(f"Fetching file from URL: {cv_url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(cv_url) as response:
            response.raise_for_status()
            user_cv_content = await response.read()

    logger.info(f"Downloaded {len(user_cv_content)} bytes from URL")
    return user_cv_content


async def generate_and_upload_pdf(storage_client, html_content):
    """
    Generate PDF from HTML content and upload it to Google Cloud Storage.

    Args:
        storage_client: Google Cloud Storage client
        html_content: HTML content to convert to PDF

    Returns:
        dict: Contains PDF URL and filename
    """
    # Generate random ID and timestamp
    random_id_1 = uuid.uuid4().hex[:32]  # First part of the filename
    pdf_filename = f"{random_id_1}.pdf"
    pdf_cloud_path = f"generated_cv/{pdf_filename}"

    logger.info(f"Starting PDF generation for {pdf_filename}")

    # Get bucket
    bucket = storage_client.bucket("main-storage-hireon")

    # Generate PDF and upload
    def generate_and_upload():
        # Generate PDF in memory
        logger.info("Generating PDF in memory")
        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        # Upload PDF
        logger.info(f"Uploading PDF to {pdf_cloud_path}")
        pdf_blob = bucket.blob(pdf_cloud_path)
        pdf_blob.upload_from_file(pdf_buffer, content_type="application/pdf")

        # Make the blob publicly accessible
        logger.info("Making blob publicly accessible")
        pdf_blob.make_public()

        # Get the public URL
        public_url = pdf_blob.public_url
        logger.info(f"PDF available at: {public_url}")

        return {
            "pdf_url": public_url,
            "pdf_cloud_path": pdf_cloud_path,
            "pdf_filename": pdf_filename,
        }

    # Run PDF generation and upload in a separate thread
    logger.info("Running PDF generation in separate thread")
    result = await asyncio.to_thread(generate_and_upload)
    logger.info("PDF generation and upload completed successfully")

    return result
