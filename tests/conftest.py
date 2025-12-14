"""
Pytest fixtures for Air Quality ETL Pipeline tests.
"""

import pytest
from datetime import datetime, timezone

from domain.models import Measurement, Place, AirQualityParameter, SensorInfo
from adapters.storage.csv_writer import CSVWriter


@pytest.fixture
def sample_measurement() -> Measurement:
    """Single valid measurement for testing."""
    return Measurement(
        city="Warsaw",
        location="Warszawa, ul. Marszałkowska",
        parameter=AirQualityParameter.PM25,
        value=15.5,
        unit="µg/m³",
        timestamp=datetime(2025, 12, 14, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_measurements() -> list[Measurement]:
    """List of measurements for different parameters."""
    timestamp = datetime(2025, 12, 14, 12, 0, tzinfo=timezone.utc)
    return [
        Measurement(
            city="Warsaw",
            location="Station A",
            parameter=AirQualityParameter.PM25,
            value=15.5,
            unit="µg/m³",
            timestamp=timestamp,
        ),
        Measurement(
            city="Warsaw",
            location="Station B",
            parameter=AirQualityParameter.PM10,
            value=25.0,
            unit="µg/m³",
            timestamp=timestamp,
        ),
        Measurement(
            city="London",
            location="Station C",
            parameter=AirQualityParameter.NO2,
            value=34.0,
            unit="µg/m³",
            timestamp=timestamp,
        ),
    ]


@pytest.fixture
def csv_writer() -> CSVWriter:
    """CSVWriter instance for testing."""
    return CSVWriter()
