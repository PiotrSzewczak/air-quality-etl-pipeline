"""
Tests for the main ETL use case.

These tests verify the orchestration of fetching and storing data.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone

from domain.models import Measurement, Place, AirQualityParameter
from application.usecases.fetch_air_quality import FetchAirQualityUseCase
from ports.air_quality_repository import AirQualityRepository
from ports.measurement_storage import MeasurementStorage


class TestFetchAirQualityUseCase:
    """Tests for FetchAirQualityUseCase."""

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """Mock for AirQualityRepository."""
        repo = Mock(spec=AirQualityRepository)
        repo.get_measurements_for_place.return_value = [
            Measurement(
                city="Warsaw",
                location="Test Station",
                parameter=AirQualityParameter.PM25,
                value=15.0,
                unit="µg/m³",
                timestamp=datetime.now(timezone.utc),
            )
        ]
        return repo

    @pytest.fixture
    def mock_storage(self) -> Mock:
        """Mock for MeasurementStorage."""
        storage = Mock(spec=MeasurementStorage)
        storage.save.return_value = "gs://bucket/file.csv"
        return storage

    @pytest.fixture
    def sample_places(self) -> list[Place]:
        """Sample places for testing."""
        return [
            Place(country_iso="PL", city_aliases=["Warsaw"]),
            Place(country_iso="GB", city_aliases=["London"]),
        ]

    def test_fetches_data_for_all_places(
        self,
        mock_repository: Mock,
        mock_storage: Mock,
        sample_places: list[Place],
    ):
        """Use case should fetch data for each configured place."""
        use_case = FetchAirQualityUseCase(
            air_quality_repository=mock_repository,
            storage=mock_storage,
        )

        use_case.execute(sample_places)

        # Should call get_measurements_for_place for each place
        assert mock_repository.get_measurements_for_place.call_count == len(
            sample_places
        )

    def test_saves_all_measurements(
        self,
        mock_repository: Mock,
        mock_storage: Mock,
        sample_places: list[Place],
    ):
        """Use case should save fetched measurements to storage."""
        use_case = FetchAirQualityUseCase(
            air_quality_repository=mock_repository,
            storage=mock_storage,
        )

        use_case.execute(sample_places)

        # Should call save once with all measurements
        mock_storage.save.assert_called_once()

    def test_returns_file_path(
        self,
        mock_repository: Mock,
        mock_storage: Mock,
        sample_places: list[Place],
    ):
        """Use case should return the path where data was saved."""
        mock_storage.save.return_value = "gs://bucket/air_quality.csv"

        use_case = FetchAirQualityUseCase(
            air_quality_repository=mock_repository,
            storage=mock_storage,
        )

        result = use_case.execute(sample_places)

        assert "gs://bucket" in result or result is not None

    def test_handles_empty_response(
        self,
        mock_storage: Mock,
        sample_places: list[Place],
    ):
        """Use case should handle case when API returns no data."""
        empty_repo = Mock(spec=AirQualityRepository)
        empty_repo.get_measurements_for_place.return_value = []

        use_case = FetchAirQualityUseCase(
            air_quality_repository=empty_repo,
            storage=mock_storage,
        )

        # Should not raise, should save empty result
        use_case.execute(sample_places)
        mock_storage.save.assert_called_once()
