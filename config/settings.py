from pathlib import Path
from decouple import config


BASE_DIR = Path(__file__).resolve().parent.parent

# OpenAQ API Configuration
BASE_OPENAQ_URL = config("BASE_OPENAQ_URL", default="https://api.openaq.org/v3")
OPENAQ_API_KEY = config("OPENAQ_API_KEY")

# Number of localities to fetch per place
NUMBER_OF_LOCALITIES_PER_PLACE = config(
    "NUMBER_OF_LOCALITIES_PER_PLACE", default=3, cast=int
)

# Google Cloud Platform Configuration
GCS_BUCKET_NAME = config("GCS_BUCKET_NAME", default="")
GCS_CREDENTIALS_PATH = config(
    "GCS_CREDENTIALS_PATH",
    default=str(BASE_DIR / "service-account.json"),
)

# Local data output directory
DATA_OUTPUT_DIR = config("DATA_OUTPUT_DIR", default=str(BASE_DIR / "data_in"))
