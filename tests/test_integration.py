"""
Integration tests for Air Quality ETL Pipeline.

Tests verify integration between components using mocks for external services.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import requests

from domain.models import Measurement, Place, AirQualityParameter
from domain.exceptions import APIError, RateLimitError
from application.usecases.fetch_air_quality import FetchAirQualityUseCase
from adapters.openaq.openaq_repository import OpenAQRepository
from adapters.storage.local_storage import LocalStorage
from adapters.storage.gcs_storage import GCSStorage


class TestOpenAQRepositoryIntegration:
    """Integration tests for OpenAQ Repository with mocked HTTP."""

    def test_filters_locations_by_city_aliases(self):
        """Test that only matching city locations are processed."""
        repo = OpenAQRepository(
            base_url="https://api.openaq.org/v3", api_key="test-key"
        )
        repo.session = Mock()

        locations_resp = Mock(status_code=200)
        locations_resp.json.return_value = {
            "results": [
                {
                    "id": 1,
                    "name": "Warsaw Station",
                    "locality": "Warsaw",
                    "sensors": [
                        {"id": 101, "parameter": {"name": "pm25", "units": "µg/m³"}}
                    ],
                },
                {
                    "id": 2,
                    "name": "Krakow Station",
                    "locality": "Krakow",
                    "sensors": [
                        {"id": 201, "parameter": {"name": "pm25", "units": "µg/m³"}}
                    ],
                },
            ]
        }
        locations_resp.raise_for_status = Mock()

        latest_resp = Mock(status_code=200)
        latest_resp.json.return_value = {
            "results": [
                {
                    "sensorsId": 101,
                    "value": 25.5,
                    "datetime": {"utc": "2025-12-14T12:00:00Z"},
                }
            ]
        }
        latest_resp.raise_for_status = Mock()

        repo.session.get.side_effect = [locations_resp, latest_resp]

        place = Place(country_iso="PL", city_aliases=["Warsaw", "Warszawa"])
        measurements = repo.get_measurements_for_place(place, locations_limit=3)

        assert len(measurements) == 1
        assert measurements[0].city == "Warsaw"

    def test_raises_rate_limit_error_on_429(self):
        """Test proper exception for rate limiting."""
        repo = OpenAQRepository(
            base_url="https://api.openaq.org/v3", api_key="test-key"
        )
        repo.session = Mock()

        mock_resp = Mock(status_code=429, text="Rate limit exceeded")
        mock_resp.raise_for_status.side_effect = requests.HTTPError(
            "429 Too Many Requests"
        )
        repo.session.get.return_value = mock_resp

        with pytest.raises(RateLimitError):
            repo.get_countries()


class TestGCSStorageIntegration:
    """Integration test for GCS Storage."""

    @patch("adapters.storage.gcs_storage.storage.Client")
    @patch(
        "adapters.storage.gcs_storage.service_account.Credentials.from_service_account_file"
    )
    def test_uploads_csv_to_bucket(self, mock_creds, mock_client, sample_measurements):
        """Test that CSV is uploaded to GCS bucket."""
        mock_creds.return_value = Mock()
        mock_blob = Mock()
        mock_client.return_value.bucket.return_value.blob.return_value = mock_blob

        storage = GCSStorage(
            bucket_name="test-bucket", credentials_path="/path/creds.json"
        )
        result = storage.save(sample_measurements)

        assert result.startswith("gs://test-bucket/")
        mock_blob.upload_from_string.assert_called_once()


class TestFullPipelineIntegration:
    """End-to-end pipeline integration test."""

    def test_fetches_validates_and_stores_measurements(self, tmp_path):
        """Test complete ETL flow with validation filtering."""
        mock_repo = Mock()
        mock_repo.get_measurements_for_place.return_value = [
            Measurement(
                city="Warsaw",
                location="Station A",
                parameter=AirQualityParameter.PM25,
                value=25.5,
                unit="µg/m³",
                timestamp=datetime(2025, 12, 14, 12, 0, tzinfo=timezone.utc),
            ),
            Measurement(  # Invalid - negative value
                city="Warsaw",
                location="Station B",
                parameter=AirQualityParameter.PM10,
                value=-10.0,
                unit="µg/m³",
                timestamp=datetime(2025, 12, 14, 12, 0, tzinfo=timezone.utc),
            ),
        ]

        storage = LocalStorage(output_dir=str(tmp_path))
        use_case = FetchAirQualityUseCase(
            air_quality_repository=mock_repo, storage=storage
        )

        place = Place(country_iso="PL", city_aliases=["Warsaw"])
        result = use_case.execute([place], locations_limit=3)

        with open(result, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 2  # Header + 1 valid measurement
        assert "Station A" in lines[1]
