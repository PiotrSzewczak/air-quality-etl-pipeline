"""
OpenAQ Repository Adapter

This module implements the AirQualityRepository port for the OpenAQ API,
fetching air quality measurements from monitoring stations.
"""

import logging
from datetime import datetime
from typing import Optional

import requests

from domain.models import AirQualityParameter, Measurement, Place, SensorInfo
from domain.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from ports.air_quality_repository import AirQualityRepository
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Parameters required for air quality monitoring
REQUIRED_PARAMETERS = [
    AirQualityParameter.PM25,
    AirQualityParameter.PM10,
    AirQualityParameter.O3,
    AirQualityParameter.NO2,
]


class OpenAQRepository(AirQualityRepository):
    """
    OpenAQ API adapter implementing the AirQualityRepository port.

    Fetches air quality measurements from the OpenAQ platform.

    Attributes:
        BASE_URL: The base URL for the OpenAQ API.
        session: A requests session with authentication headers.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        """
        Initialize the OpenAQ client.

        Args:
            base_url: The base URL for the OpenAQ API.
            api_key: API key for authentication.
        """
        self.BASE_URL = base_url
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})

    def _handle_response(self, response: requests.Response) -> dict:
        """
        Handle API response and raise appropriate exceptions for errors.

        Args:
            response: The HTTP response object from the API.

        Returns:
            The parsed JSON response.

        Raises:
            AuthenticationError: For 401/403 status codes.
            NotFoundError: For 404 status codes.
            RateLimitError: For 429 status codes.
            APIError: For other error status codes.
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            status_code = response.status_code
            response_body = response.text

            if status_code in (401, 403):
                logger.error(f"Authentication failed: {response_body}")
                raise AuthenticationError(
                    f"Authentication failed: {e}",
                    status_code=status_code,
                    response_body=response_body,
                ) from e
            elif status_code == 404:
                logger.warning(f"Resource not found: {response.url}")
                raise NotFoundError(
                    f"Resource not found: {e}",
                    status_code=status_code,
                    response_body=response_body,
                ) from e
            elif status_code == 429:
                logger.warning(f"Rate limit exceeded: {response_body}")
                raise RateLimitError(
                    f"Rate limit exceeded: {e}",
                    status_code=status_code,
                    response_body=response_body,
                ) from e
            else:
                logger.error(f"API error ({status_code}): {response_body}")
                raise APIError(
                    f"API request failed: {e}",
                    status_code=status_code,
                    response_body=response_body,
                ) from e

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_countries(self) -> list[dict]:
        """
        Fetch all available countries from the API.

        Returns:
            A list of country dictionaries containing country information.

        Raises:
            APIError: If the API request fails after all retries.
        """
        logger.debug("Fetching countries from OpenAQ API")
        response = self.session.get(f"{self.BASE_URL}/countries")
        data = self._handle_response(response)
        logger.info(f"Successfully fetched {len(data['results'])} countries")
        return data["results"]

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_locations(self, country_iso: str) -> list[dict]:
        """
        Fetch all monitoring locations for a specific country.

        Args:
            country_iso: ISO 3166-1 alpha-2 country code (e.g., 'PL', 'GB').

        Returns:
            A list of location dictionaries containing station information.

        Raises:
            APIError: If the API request fails after all retries.
        """
        logger.debug(f"Fetching locations for country: {country_iso}")
        response = self.session.get(
            f"{self.BASE_URL}/locations",
            params={"iso": country_iso, "limit": 1000},
        )
        data = self._handle_response(response)
        logger.info(
            f"Successfully fetched {len(data['results'])} locations for {country_iso}"
        )
        return data["results"]

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def get_latest_for_location(self, location_id: int) -> list[dict]:
        """
        Fetch the latest measurements for a specific location.

        Args:
            location_id: The unique identifier of the monitoring station.

        Returns:
            A list of measurement dictionaries with the latest readings.

        Raises:
            APIError: If the API request fails after all retries.
            NotFoundError: If the location does not exist.
        """
        logger.debug(f"Fetching latest measurements for location: {location_id}")
        response = self.session.get(f"{self.BASE_URL}/locations/{location_id}/latest")
        data = self._handle_response(response)
        logger.debug(
            f"Fetched {len(data['results'])} measurements for location {location_id}"
        )
        return data["results"]

    def _build_sensor_parameter_map(self, location: dict) -> dict[int, SensorInfo]:
        """
        Build a mapping from sensor IDs to sensor info (parameter + unit).

        Extracts sensor information from a location and creates a dictionary
        that maps each sensor ID to its corresponding SensorInfo containing
        AirQualityParameter enum and unit string.
        Only sensors with recognized parameters are included.

        Args:
            location: A location dictionary containing sensor information.

        Returns:
            A dictionary mapping sensor IDs to SensorInfo objects.
        """
        mapping: dict[int, SensorInfo] = {}

        for sensor in location.get("sensors", []):
            param_data = sensor.get("parameter", {})
            param_name = param_data.get("name")
            unit = param_data.get("units", "µg/m³")

            if not param_name:
                continue

            try:
                mapping[sensor["id"]] = SensorInfo(
                    parameter=AirQualityParameter(param_name),
                    unit=unit,
                )
            except ValueError:
                # Parameter not in our domain, skip it
                continue

        return mapping

    def _get_latest_measurements_by_location(
        self, location: dict
    ) -> dict[AirQualityParameter, Optional[Measurement]]:
        """
        Fetch the latest measurements for all required parameters at a location.

        Retrieves the most recent air quality readings for PM2.5, PM10, O3, and NO2
        from the specified monitoring station. Parameters without available data
        are returned as None.

        Args:
            location: A location dictionary containing station information
                      including 'id', 'name', 'locality', and 'sensors'.

        Returns:
            A dictionary mapping each required AirQualityParameter to its
            latest Measurement object, or None if data is unavailable.
        """
        # Initialize result with None for all required parameters
        result: dict[AirQualityParameter, Optional[Measurement]] = {
            param: None for param in REQUIRED_PARAMETERS
        }

        # Build sensor ID to parameter mapping
        sensor_map = self._build_sensor_parameter_map(location)

        # Fetch latest measurements from API
        latest_results = self.get_latest_for_location(location["id"])

        for item in latest_results:
            sensor_id = item.get("sensorsId")
            if sensor_id not in sensor_map:
                continue

            sensor_info = sensor_map[sensor_id]
            if sensor_info.parameter not in result:
                continue

            result[sensor_info.parameter] = Measurement(
                city=location.get("locality"),
                location=location.get("name"),
                parameter=sensor_info.parameter,
                value=float(item["value"]),
                unit=sensor_info.unit,
                timestamp=datetime.fromisoformat(
                    item["datetime"]["utc"].replace("Z", "+00:00")
                ),
            )

        return result

    def _location_matches_place(self, loc: dict, place: Place) -> bool:
        """
        Check if a location matches any of the city aliases in a Place.
        """
        aliases = {a.lower() for a in place.city_aliases}

        locality = (loc.get("locality") or "").lower()
        name = (loc.get("name") or "").lower()

        return locality in aliases or any(alias in name for alias in aliases)

    def get_measurements_for_place(
        self, place: Place, locations_limit: int = 3
    ) -> list[Measurement]:
        """
        Fetch the latest air quality measurements for a place.

        Retrieves the most recent readings for PM2.5, PM10, O3, and NO2
        from monitoring stations matching the specified place criteria
        (country ISO code and city aliases).

        Args:
            place: A Place object containing country ISO code and city aliases
                   used to filter monitoring stations.
            locations_limit: Maximum number of stations to query. Defaults to 3.
                             Useful for limiting API calls and focusing on
                             the most relevant stations.

        Returns:
            A list of Measurement objects from all matched stations.
            Only non-null measurements are included.
        """
        all_measurements: list[Measurement] = []

        # Fetch all locations for the country
        locations = self.get_locations(place.country_iso)

        # Filter locations matching the place criteria
        filtered_locations = [
            loc for loc in locations if self._location_matches_place(loc, place)
        ]

        # Collect measurements from up to `locations_limit` stations
        for location in filtered_locations[:locations_limit]:
            measurements_map = self._get_latest_measurements_by_location(location)
            for measurement in measurements_map.values():
                if measurement is not None:
                    all_measurements.append(measurement)

        return all_measurements
