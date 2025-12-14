"""
Tests for data validation logic.

These tests verify that invalid measurements are properly rejected.
"""

import pytest
from datetime import datetime, timezone

from domain.models import Measurement, AirQualityParameter
from domain.validators import validate_measurement
from domain.exceptions import ValidationError


class TestValidateMeasurement:
    """Tests for validate_measurement function."""

    def test_valid_measurement_passes(self, sample_measurement: Measurement):
        """Valid measurement should pass validation without raising."""
        # Should not raise any exception
        validate_measurement(sample_measurement)

    def test_rejects_negative_value(self):
        """Negative values are physically impossible for air quality."""
        measurement = Measurement(
            city="Warsaw",
            location="Test",
            parameter=AirQualityParameter.PM25,
            value=-5.0,
            unit="µg/m³",
            timestamp=datetime.now(timezone.utc),
        )

        with pytest.raises(ValidationError):
            validate_measurement(measurement)

    def test_rejects_empty_city(self):
        """City name cannot be empty."""
        measurement = Measurement(
            city="",
            location="Test",
            parameter=AirQualityParameter.PM25,
            value=10.0,
            unit="µg/m³",
            timestamp=datetime.now(timezone.utc),
        )

        with pytest.raises(ValidationError):
            validate_measurement(measurement)

    def test_rejects_none_timestamp(self):
        """Timestamp is required for time-series data."""
        measurement = Measurement(
            city="Warsaw",
            location="Test",
            parameter=AirQualityParameter.PM25,
            value=10.0,
            unit="µg/m³",
            timestamp=None,
        )

        with pytest.raises(ValidationError):
            validate_measurement(measurement)

    def test_accepts_zero_value(self):
        """Zero is a valid measurement value."""
        measurement = Measurement(
            city="Warsaw",
            location="Test",
            parameter=AirQualityParameter.PM25,
            value=0.0,
            unit="µg/m³",
            timestamp=datetime.now(timezone.utc),
        )

        # Should not raise
        validate_measurement(measurement)
