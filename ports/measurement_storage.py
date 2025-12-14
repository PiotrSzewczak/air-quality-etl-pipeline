"""
Measurement Storage Port

This module defines the interface for storing air quality measurements.
Adapters must implement this interface.
"""

from abc import ABC, abstractmethod

from domain.models import Measurement


class MeasurementStorage(ABC):
    """
    Abstract interface for measurement storage.

    This port defines the contract that any storage provider
    must implement (e.g., GCS, S3, local filesystem).
    """

    @abstractmethod
    def save(self, measurements: list[Measurement]) -> str:
        """
        Save measurements to storage.

        Args:
            measurements: List of Measurement objects to save.

        Returns:
            The path/URI where the data was saved.
        """
        pass
