"""
Storage Adapters

This module exports storage adapters for measurement data.
"""

from adapters.storage.gcs_storage import GCSStorage
from adapters.storage.local_storage import LocalStorage

__all__ = ["GCSStorage", "LocalStorage"]
