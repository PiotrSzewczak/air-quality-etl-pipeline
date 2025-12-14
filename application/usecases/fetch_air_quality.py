import logging
from typing import Optional

from domain.models import Place, Measurement
from domain.exceptions import ValidationError
from ports.air_quality_repository import AirQualityRepository
from ports.measurement_storage import MeasurementStorage
from ports.data_warehouse_loader import DataWarehouseLoader
from domain.validators import validate_measurement


class FetchAirQualityUseCase:
    """
    Use case for fetching air quality measurements and storing them.

    Coordinates between the air quality repository (data source)
    and measurement storage (data destination).
    """

    def __init__(
        self,
        air_quality_repository: AirQualityRepository,
        storage: MeasurementStorage,
        data_warehouse_loader: Optional[DataWarehouseLoader] = None,
    ):
        self.air_quality_repository = air_quality_repository
        self.storage = storage
        self.data_warehouse_loader = data_warehouse_loader
        self.logger = logging.getLogger(__name__)

    def fetch_measurements(
        self, places_list: list[Place], locations_limit: int
    ) -> list[Measurement]:
        """
        Fetch and validate measurements for given places.

        Args:
            places_list: List of places to fetch measurements for.

        Returns:
            List of validated measurements.
        """
        all_measurements: list[Measurement] = []

        for place in places_list:
            measurements = self.air_quality_repository.get_measurements_for_place(
                place, locations_limit
            )
            valid_measurements = []
            for measurement in measurements:
                try:
                    validate_measurement(measurement)
                    valid_measurements.append(measurement)
                except ValidationError as ve:
                    self.logger.error(
                        f"Validation error for measurement {measurement}: {ve}"
                    )
                    continue  # Skip invalid measurement
            all_measurements.extend(valid_measurements)
        return all_measurements

    def execute(self, places_list: list[Place], locations_limit: int = 3) -> str:
        """
        Execute the full ETL pipeline: fetch, validate, and store measurements.

        Args:
            places_list: List of places to process.

        Returns:
            Path/URI where the data was saved.
        """
        self.logger.info(f"Fetching measurements for {len(places_list)} places")

        # Fetch and validate measurements
        measurements = self.fetch_measurements(
            places_list=places_list, locations_limit=locations_limit
        )
        self.logger.info(f"Fetched {len(measurements)} valid measurements")

        # Store measurements
        output_path = self.storage.save(measurements)
        self.logger.info(f"Saved measurements to: {output_path}")

        # Load to data warehouse if configured
        if self.data_warehouse_loader and output_path.startswith("gs://"):
            rows_loaded = self.data_warehouse_loader.load_from_gcs(output_path)
            self.logger.info(f"Loaded {rows_loaded} rows to data warehouse")

        return output_path
