"""
BigQuery Factory

This module provides a factory function to create the BigQuery loader adapter.
"""

from typing import Optional

from adapters.bigquery.bigquery_loader import BigQueryLoader
from config.settings import (
    BIGQUERY_PROJECT_ID,
    BIGQUERY_DATASET_ID,
    BIGQUERY_TABLE_ID,
    BIGQUERY_ENABLED,
    GCS_CREDENTIALS_PATH,
)


def create_bigquery_loader() -> Optional[BigQueryLoader]:
    """
    Create BigQuery loader if enabled and configured.

    Returns:
        BigQueryLoader instance or None if disabled/misconfigured.
    """
    if not (BIGQUERY_ENABLED and BIGQUERY_PROJECT_ID):
        return None

    return BigQueryLoader(
        project_id=BIGQUERY_PROJECT_ID,
        dataset_id=BIGQUERY_DATASET_ID,
        table_id=BIGQUERY_TABLE_ID,
        credentials_path=GCS_CREDENTIALS_PATH,
    )
