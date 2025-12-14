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
    if GCS_BUCKET_NAME and os.path.exists(GCS_CREDENTIALS_PATH):
        logger.info(f"Using GCS storage (bucket: {GCS_BUCKET_NAME})")
        return GCSStorage(
            bucket_name=GCS_BUCKET_NAME,
            credentials_path=GCS_CREDENTIALS_PATH,
        )

    if GCS_BUCKET_NAME:
        logger.warning(
            f"GCS credentials not found at: {GCS_CREDENTIALS_PATH}. "
            "Falling back to local storage."
        )

    logger.info(f"Using local storage only (output: {DATA_OUTPUT_DIR})")
    return LocalStorage(output_dir=DATA_OUTPUT_DIR)
