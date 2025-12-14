"""
Storage Factory
This module provides a factory function to create the appropriate
measurement storage adapter based on configuration.
"""

import os
import logging

from config.settings import (
    GCS_BUCKET_NAME,
    GCS_CREDENTIALS_PATH,
    DATA_OUTPUT_DIR,
)
from adapters.storage.gcs_storage import GCSStorage
from adapters.storage.local_storage import LocalStorage
from ports.measurement_storage import MeasurementStorage

logger = logging.getLogger(__name__)


def create_storage() -> MeasurementStorage:
    """
    Create storage adapter based on configuration.

    Prioritizes GCS if bucket name is configured.
    Supports both Service Account file and ADC (if credentials path is None).
    Falls back to local storage if GCS config is invalid or missing.
    """
    if GCS_BUCKET_NAME:
        # Case 1: Credentials file provided
        if GCS_CREDENTIALS_PATH:
            if os.path.exists(GCS_CREDENTIALS_PATH):
                logger.info(
                    f"Using GCS storage (bucket: {GCS_BUCKET_NAME}) with credentials file"
                )
                return GCSStorage(
                    bucket_name=GCS_BUCKET_NAME,
                    credentials_path=GCS_CREDENTIALS_PATH,
                )
            else:
                logger.warning(
                    f"GCS credentials configured but not found at: {GCS_CREDENTIALS_PATH}. "
                    "Falling back to local storage."
                )
        # Case 2: No credentials file provided (ADC)
        else:
            logger.info(f"Using GCS storage (bucket: {GCS_BUCKET_NAME}) with ADC")
            return GCSStorage(
                bucket_name=GCS_BUCKET_NAME,
                credentials_path=None,
            )

    logger.info(f"Using local storage only (output: {DATA_OUTPUT_DIR})")
    return LocalStorage(output_dir=DATA_OUTPUT_DIR)
