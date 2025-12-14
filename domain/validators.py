from datetime import datetime, timezone

from domain.models import Measurement
from domain.exceptions import ValidationError


def validate_measurement(measurement: Measurement) -> None:
    if not measurement.city:
        raise ValidationError("City is required")

    if not measurement.location:
        raise ValidationError("Location is required")

    if measurement.parameter is None:
        raise ValidationError("Parameter is required")

    if measurement.value is None:
        raise ValidationError("Measurement value is required")

    if measurement.value < 0:
        raise ValidationError("Measurement value cannot be negative")

    if not measurement.unit:
        raise ValidationError("Unit is required")

    if not isinstance(measurement.timestamp, datetime):
        raise ValidationError("Timestamp must be datetime")

    if measurement.timestamp > datetime.now(timezone.utc):
        raise ValidationError("Timestamp cannot be in the future")
