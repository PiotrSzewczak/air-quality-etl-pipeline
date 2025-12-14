"""
Domain Models
This module defines the core domain models for the air quality ETL pipeline.
These models represent the main entities used throughout the application.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AirQualityParameter(str, Enum):
    """Supported air quality parameters."""

    PM25 = "pm25"
    PM10 = "pm10"
    O3 = "o3"
    NO2 = "no2"


@dataclass(frozen=True)
class Place:
    """Represents a geographic location for air quality monitoring."""

    country_iso: str
    city_aliases: list[str]


@dataclass
class Measurement:
    """Represents a single air quality measurement reading."""

    city: str
    location: str
    parameter: AirQualityParameter
    value: float
    unit: str
    timestamp: datetime


@dataclass(frozen=True)
class SensorInfo:
    """Sensor metadata including parameter type and unit."""

    parameter: AirQualityParameter
    unit: str
