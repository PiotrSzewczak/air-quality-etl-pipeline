"""
Data Warehouse Loader Port

This module defines the abstract interface for loading data into a data warehouse.
"""

from abc import ABC, abstractmethod


class DataWarehouseLoader(ABC):
    """
    Abstract interface for data warehouse loading operations.

    Implementations of this interface handle the transfer of data
    from storage (e.g., GCS) into analytical data warehouses.
    """

    @abstractmethod
    def load_from_gcs(self, gcs_uri: str) -> int:
        """
        Load data from a GCS file into the data warehouse.

        Args:
            gcs_uri: GCS URI of the source file.

        Returns:
            Number of rows loaded.
        """
        pass
