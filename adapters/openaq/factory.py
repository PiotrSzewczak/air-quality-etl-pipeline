"""
OpenAQ Factory

This module provides a factory function to create the OpenAQ repository adapter.
"""

from adapters.openaq.openaq_repository import OpenAQRepository
from config.settings import BASE_OPENAQ_URL, OPENAQ_API_KEY


def create_openaq_repository() -> OpenAQRepository:
    """
    Create OpenAQ repository adapter.

    Returns:
        Configured OpenAQRepository instance.
    """
    return OpenAQRepository(base_url=BASE_OPENAQ_URL, api_key=OPENAQ_API_KEY)
