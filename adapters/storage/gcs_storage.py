"""
Google Cloud Storage Adapter

This module implements the MeasurementStorage port for Google Cloud Storage.
Uses service account key for authentication.
"""

import logging
from typing import Optional

from google.cloud import storage
from google.oauth2 import service_account

from domain.models import Measurement
from ports.measurement_storage import MeasurementStorage
from adapters.storage.csv_writer import CSVWriter


class GCSStorage(MeasurementStorage):
    """
    Google Cloud Storage adapter for measurement storage.

    Saves measurements as CSV files to GCS bucket.
    Uses service account credentials for authentication.
    """

    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize GCS storage adapter.

        Args:
            bucket_name: Name of the GCS bucket.
            credentials_path: Path to service account JSON key file.
                              If None, uses Application Default Credentials.
        """
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.logger = logging.getLogger(__name__)
        self.csv_writer = CSVWriter()

        # Initialize GCS client
        if credentials_path:
            self.logger.info(f"Using service account file: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = storage.Client(credentials=credentials)
        else:
            self.logger.info("Using Application Default Credentials (ADC)")
            self.client = storage.Client()

        self.bucket = self.client.bucket(bucket_name)

    def save(self, measurements: list[Measurement]) -> str:
        """
        Save measurements to GCS.

        Args:
            measurements: List of Measurement objects to save.

        Returns:
            The GCS URI where the data was saved.
        """
        if not measurements:
            self.logger.warning("No measurements to save")
            return ""

        # Generate CSV content
        csv_content, filename = self.csv_writer.generate(measurements)

        # Upload to GCS
        gcs_uri = self._upload_to_gcs(csv_content, filename)
        self.logger.info(f"Uploaded to GCS: {gcs_uri}")

        return gcs_uri

    def _upload_to_gcs(self, content: bytes, filename: str) -> str:
        """
        Upload CSV content to Google Cloud Storage.

        Args:
            content: CSV content as bytes.
            filename: Name of the file in GCS.

        Returns:
            GCS URI (gs://bucket/filename).
        """
        blob = self.bucket.blob(filename)
        blob.upload_from_string(content, content_type="text/csv; charset=utf-8")
        return f"gs://{self.bucket_name}/{filename}"
