"""
Air Quality ETL Pipeline - Main Entry Point

This script fetches air quality data from OpenAQ API for configured cities,
saves it locally as CSV, and optionally uploads to Google Cloud Storage.

Can be deployed as a Google Cloud Function for automated data loading.
"""

import logging

from adapters.openaq import OpenAQRepository
from adapters.storage.factory import create_storage
from application.usecases.fetch_air_quality import FetchAirQualityUseCase
from config.places import PLACES
from config.settings import (
    BASE_OPENAQ_URL,
    OPENAQ_API_KEY,
    NUMBER_OF_LOCALITIES_PER_PLACE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main(request=None) -> dict:
    """
    Main entry point for the air quality data pipeline.

    Can be invoked directly or as a Cloud Function.

    Args:
        request: HTTP request object (for Cloud Function invocation).

    Returns:
        Dictionary with execution result.
    """
    logger.info("Starting air quality ETL pipeline")

    # Initialize adapters
    openaq_repository = OpenAQRepository(
        base_url=BASE_OPENAQ_URL, api_key=OPENAQ_API_KEY
    )

    storage = create_storage()

    # Create and execute use case
    use_case = FetchAirQualityUseCase(
        air_quality_repository=openaq_repository,
        storage=storage,
    )

    output_path = use_case.execute(
        places_list=PLACES, locations_limit=NUMBER_OF_LOCALITIES_PER_PLACE
    )

    result = {
        "status": "success",
        "output_path": output_path,
        "cities": [p.city_aliases[0] for p in PLACES],
    }

    logger.info(f"Pipeline completed: {result}")
    return result


if __name__ == "__main__":
    main()
