import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# OpenAQ API Configuration
BASE_OPENAQ_URL = os.getenv("BASE_OPENAQ_URL", "https://api.openaq.org/v3")
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")

# Number of localities to fetch per place
NUMBER_OF_LOCALITIES_PER_PLACE = int(os.getenv("NUMBER_OF_LOCALITIES_PER_PLACE", "3"))

# Google Cloud Platform Configuration
GOOGLE_CLOUD_PROJECT = os.getenv("BIGQUERY_PROJECT_ID")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH")

# Local data output directory
DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR", str(BASE_DIR / "data_in"))

# BigQuery Configuration
BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "")
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "air_quality")
BIGQUERY_TABLE_ID = os.getenv("BIGQUERY_TABLE_ID", "measurements")
BIGQUERY_ENABLED = os.getenv("BIGQUERY_ENABLED", "false").lower() in (
    "true",
    "1",
    "yes",
)
