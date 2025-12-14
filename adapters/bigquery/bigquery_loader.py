"""
BigQuery Loader Adapter

This module provides functionality to load CSV data from GCS into BigQuery.
Designed for automated, cyclic data warehouse loading.
"""

import logging
from typing import Optional

from google.cloud import bigquery
from google.oauth2 import service_account

from ports.data_warehouse_loader import DataWarehouseLoader

SCHEMA = [
    bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("location", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("parameter", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("value", "FLOAT64", mode="REQUIRED"),
    bigquery.SchemaField("unit", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
]


class BigQueryLoader(DataWarehouseLoader):
    """
    Loads data from GCS CSV files into BigQuery.

    This adapter handles the transfer of CSV files stored in Google Cloud Storage
    to BigQuery tables, supporting both append and overwrite modes.
    """

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize BigQuery loader.

        Args:
            project_id: GCP project ID.
            dataset_id: BigQuery dataset ID.
            table_id: BigQuery table ID.
            credentials_path: Path to service account JSON key file.
                              If None, uses default credentials (for Cloud Functions).
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        self.logger = logging.getLogger(__name__)

        # Initialize BigQuery client
        if credentials_path:
            self.logger.info(f"Using service account file for BQ: {credentials_path}")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            # For Cloud Functions - uses default credentials
            self.logger.info("Using Application Default Credentials (ADC) for BQ")
            self.client = bigquery.Client(project=project_id)

    def load_from_gcs(self, gcs_uri: str) -> int:
        """
        Load CSV data from GCS into BigQuery table.

        Creates the table if it doesn't exist, using schema auto-detection.
        Appends data to existing table.

        Args:
            gcs_uri: GCS URI of the CSV file (gs://bucket/filename.csv).

        Returns:
            Number of rows loaded.

        Raises:
            google.cloud.exceptions.GoogleCloudError: If loading fails.
        """
        self.logger.info(f"Loading {gcs_uri} into {self.full_table_id}")

        # Ensure table exists before loading
        self.ensure_table_exists()

        # Define schema matching our CSV structure
        schema = SCHEMA

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,  # Skip header row
            field_delimiter=";",  # Match CSVWriter delimiter
            schema=schema,  # Use explicit schema instead of autodetect
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        load_job = self.client.load_table_from_uri(
            gcs_uri,
            self.full_table_id,
            job_config=job_config,
        )

        # Wait for the job to complete
        load_job.result()

        # Get destination table info
        destination_table = self.client.get_table(self.full_table_id)
        rows_loaded = load_job.output_rows or 0

        self.logger.info(
            f"Loaded {rows_loaded} rows into {self.full_table_id}. "
            f"Table now has {destination_table.num_rows} total rows."
        )

        return rows_loaded

    def ensure_dataset_exists(self) -> None:
        """
        Ensure the target dataset exists.

        Creates the dataset if it doesn't exist.
        """
        dataset_ref = f"{self.project_id}.{self.dataset_id}"

        try:
            self.client.get_dataset(dataset_ref)
            self.logger.info(f"Dataset {dataset_ref} already exists")
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "EU"  # Set location for EU data
            self.client.create_dataset(dataset)
            self.logger.info(f"Created dataset {dataset_ref}")

    def ensure_table_exists(self) -> None:
        """
        Ensure the target table exists with the correct schema.

        Creates the dataset and table if they don't exist.
        Uses explicit schema for air quality measurements.
        """
        # First ensure dataset exists
        self.ensure_dataset_exists()

        schema = SCHEMA

        table = bigquery.Table(self.full_table_id, schema=schema)

        try:
            self.client.get_table(self.full_table_id)
            self.logger.info(f"Table {self.full_table_id} already exists")
        except Exception:
            table = self.client.create_table(table)
            self.logger.info(f"Created table {self.full_table_id}")
