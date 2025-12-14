"""
CSV Writer for Measurement Storage

This module provides CSV generation functionality for measurement data.
It is part of the storage adapter layer as it deals with data serialization.
"""

import csv
import io
from datetime import datetime, timezone

from domain.models import Measurement


class CSVWriter:
    """
    Generates CSV content from measurement data.

    Converts a list of Measurement objects into CSV format with UTF-8 encoding.
    Uses semicolon as delimiter for better Excel compatibility.
    """

    HEADERS = [
        "city",
        "location",
        "parameter",
        "value",
        "unit",
        "timestamp",
    ]

    def generate(self, measurements: list[Measurement]) -> tuple[bytes, str]:
        """
        Generate CSV content from measurements.

        Args:
            measurements: List of Measurement objects to serialize.

        Returns:
            A tuple containing:
                - bytes: UTF-8 encoded CSV content
                - str: Generated filename with timestamp
        """
        filename = f"air_quality_{datetime.now(timezone.utc).isoformat()}.csv"

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=";")
        writer.writerow(self.HEADERS)

        for m in measurements:
            writer.writerow(
                [
                    m.city,
                    m.location,
                    m.parameter.value,
                    m.value,
                    m.unit,
                    m.timestamp.isoformat(),
                ]
            )

        return buffer.getvalue().encode("utf-8"), filename
