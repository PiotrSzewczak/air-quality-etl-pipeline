"""
Tests for CSV generation.

These tests verify correct CSV format for GCS upload.
"""

import pytest
from datetime import datetime, timezone

from domain.models import Measurement, AirQualityParameter
from adapters.storage.csv_writer import CSVWriter


class TestCSVWriter:
    """Tests for CSVWriter class."""

    def test_generates_correct_headers(
        self, csv_writer: CSVWriter, sample_measurements: list[Measurement]
    ):
        """CSV should have correct headers in first row."""
        content, _ = csv_writer.generate(sample_measurements)
        decoded = content.decode("utf-8")

        first_line = decoded.split("\n")[0].strip()
        expected = "city;location;parameter;value;unit;timestamp"

        assert first_line == expected

    def test_generates_correct_row_count(
        self, csv_writer: CSVWriter, sample_measurements: list[Measurement]
    ):
        """CSV should have header + one row per measurement."""
        content, _ = csv_writer.generate(sample_measurements)
        decoded = content.decode("utf-8")

        lines = [line for line in decoded.strip().split("\n") if line]
        # 1 header + 3 measurements
        assert len(lines) == 4

    def test_uses_semicolon_delimiter(
        self, csv_writer: CSVWriter, sample_measurement: Measurement
    ):
        """CSV should use semicolon as delimiter (European format)."""
        content, _ = csv_writer.generate([sample_measurement])
        decoded = content.decode("utf-8")

        # Data row should have 5 semicolons (6 columns)
        data_line = decoded.split("\n")[1]
        assert data_line.count(";") == 5

    def test_generates_utf8_content(
        self, csv_writer: CSVWriter, sample_measurement: Measurement
    ):
        """CSV content should be valid UTF-8 bytes."""
        content, _ = csv_writer.generate([sample_measurement])

        assert isinstance(content, bytes)
        # Should decode without errors
        decoded = content.decode("utf-8")
        assert "Warsaw" in decoded

    def test_filename_contains_timestamp(
        self, csv_writer: CSVWriter, sample_measurements: list[Measurement]
    ):
        """Generated filename should contain ISO timestamp."""
        _, filename = csv_writer.generate(sample_measurements)

        assert filename.startswith("air_quality_")
        assert filename.endswith(".csv")
        # Should contain date pattern
        assert "2025" in filename or "T" in filename

    def test_empty_list_generates_header_only(self, csv_writer: CSVWriter):
        """Empty measurement list should still produce valid CSV with headers."""
        content, _ = csv_writer.generate([])
        decoded = content.decode("utf-8")

        lines = [line for line in decoded.strip().split("\n") if line]
        assert len(lines) == 1  # Only header
