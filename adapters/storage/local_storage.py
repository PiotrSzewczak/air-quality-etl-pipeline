"""
Local Filesystem Storage Adapter

This module implements the MeasurementStorage port for local filesystem.
"""

import logging
from pathlib import Path

from domain.models import Measurement
from ports.measurement_storage import MeasurementStorage
from adapters.storage.csv_writer import CSVWriter


class LocalStorage(MeasurementStorage):
    """
    Local filesystem adapter for measurement storage.

    Saves measurements as CSV files to local directory.
    """

    def __init__(self, output_dir: str = "data_in"):
        """
        Initialize local storage adapter.

        Args:
            output_dir: Directory to save CSV files.
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self.csv_writer = CSVWriter()

    def save(self, measurements: list[Measurement]) -> str:
        """
        Save measurements to local filesystem.

        Args:
            measurements: List of Measurement objects to save.

        Returns:
            The local path where the data was saved.
        """
        if not measurements:
            self.logger.warning("No measurements to save")
            return ""

        # Generate CSV content
        csv_content, filename = self.csv_writer.generate(measurements)

        # Save locally
        self.output_dir.mkdir(parents=True, exist_ok=True)
        file_path = self.output_dir / filename
        file_path.write_bytes(csv_content)

        self.logger.info(f"Saved locally to: {file_path}")
        return str(file_path)
