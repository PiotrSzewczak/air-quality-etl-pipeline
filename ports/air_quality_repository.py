"""
Air Quality Repository Port

This module defines the interface for fetching air quality data
from external sources. Adapters must implement this interface.
"""

from abc import ABC, abstractmethod

from domain.models import Measurement, Place


class AirQualityRepository(ABC):
    """
    Abstract interface for air quality data sources.

    This port defines the contract that any air quality data provider
    must implement. The application layer depends on this abstraction,
    not on concrete implementations.
    """

    @abstractmethod
    def get_measurements_for_place(
        self, place: Place, locations_limit: int = 3
    ) -> list[Measurement]:
        """
        Fetch the latest air quality measurements for a place.

        Args:
            place: A Place object containing country ISO code and city aliases
                   used to filter monitoring stations.
            locations_limit: Maximum number of stations to query. Defaults to 3.

        Returns:
            A list of Measurement objects from matched stations.
        """
        pass
