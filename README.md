# Air Quality ETL Pipeline

A Python-based ETL (Extract, Transform, Load) pipeline that fetches air quality data from the [OpenAQ API](https://openaq.org/), processes it, and stores it in Google Cloud Storage (GCS) with optional loading to BigQuery.

Built with **Hexagonal Architecture** (Ports & Adapters) for clean separation of concerns and easy testability.

## Features

- **Fetch air quality data** for configurable cities (default: Warsaw, London)
- **Multiple pollutants**: PM2.5, PM10, O3, NO2
- **Multiple stations**: Fetches data from up to 3 monitoring stations per city
- **Data validation**: Rejects invalid measurements (negative values, missing fields)
- **Flexible storage**: Local CSV or Google Cloud Storage
- **Data warehouse integration**: Optional BigQuery loading
- **Retry mechanism**: Exponential backoff for API resilience
- **Cloud-ready**: Deployable as Google Cloud Function

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Entry Point / Cloud Function)                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│              (application/usecases/fetch_air_quality.py)         │
│                                                                  │
│   FetchAirQualityUseCase: Orchestrates the ETL pipeline          │
│   - Fetches measurements for each place                          │
│   - Validates data                                               │
│   - Saves to storage                                             │
│   - Optionally loads to BigQuery                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│      Ports        │ │     Ports       │ │       Ports         │
│  (Interfaces)     │ │  (Interfaces)   │ │   (Interfaces)      │
├───────────────────┤ ├─────────────────┤ ├─────────────────────┤
│ AirQualityRepo    │ │ MeasurementStor │ │ DataWarehouseLoader │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│     Adapters      │ │    Adapters     │ │      Adapters       │
├───────────────────┤ ├─────────────────┤ ├─────────────────────┤
│ OpenAQRepository  │ │ LocalStorage    │ │ BigQueryLoader      │
│ (openaq/)         │ │ GCSStorage      │ │ (bigquery/)         │
│                   │ │ CSVWriter       │ │                     │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   OpenAQ API      │ │  GCS / Local    │ │     BigQuery        │
│   (External)      │ │  Filesystem     │ │                     │
└───────────────────┘ └─────────────────┘ └─────────────────────┘
```

## Project Structure

```
air-quality-etl-pipeline/
├── main.py                     # Entry point (local & Cloud Function)
├── deploy.sh                   # Deployment script (tests + deploy)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
│
├── domain/                     # Business logic (no external dependencies)
│   ├── models.py               # Data models (Measurement, Place, etc.)
│   ├── validators.py           # Data validation rules
│   └── exceptions.py           # Custom exceptions
│
├── ports/                      # Interfaces (abstractions)
│   ├── air_quality_repository.py
│   ├── measurement_storage.py
│   └── data_warehouse_loader.py
│
├── adapters/                   # Implementations
│   ├── openaq/                 # OpenAQ API adapter
│   │   ├── openaq_repository.py
│   │   └── factory.py
│   ├── storage/                # Storage adapters
│   │   ├── local_storage.py
│   │   ├── gcs_storage.py
│   │   ├── csv_writer.py
│   │   └── factory.py
│   └── bigquery/               # BigQuery adapter
│       ├── bigquery_loader.py
│       └── factory.py
│
├── application/                # Use cases
│   └── usecases/
│       └── fetch_air_quality.py
│
├── config/                     # Configuration
│   ├── settings.py             # Environment-based settings
│   └── places.py               # Cities to monitor
│
├── utils/                      # Utilities
│   └── retry.py                # Retry with exponential backoff
│
└── tests/                      # Unit tests
    ├── conftest.py
    ├── test_validators.py
    ├── test_csv_writer.py
    ├── test_use_case.py
    └── test_retry.py
```

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAQ API key ([get one here](https://openaq.org/))
- Google Cloud SDK (`gcloud`) installed and configured
- Google Cloud project (for GCS/BigQuery)

### Local Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/PiotrSzewczak/air-quality-etl-pipeline.git
   cd air-quality-etl-pipeline
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install pytest  # For testing
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run the pipeline locally**
   ```bash
   python main.py
   ```

### Environment Variables

| Variable                         | Description                    | Required     |
| -------------------------------- | ------------------------------ | ------------ |
| `OPENAQ_API_KEY`                 | OpenAQ API key                 | Yes          |
| `BASE_OPENAQ_URL`                | OpenAQ API base URL            | Yes          |
| `GCS_BUCKET_NAME`                | GCS bucket for CSV storage     | For GCS      |
| `GOOGLE_CLOUD_PROJECT`           | GCP project ID                 | For BigQuery |
| `BIGQUERY_PROJECT_ID`            | BigQuery project ID            | For BigQuery |
| `BIGQUERY_ENABLED`               | Enable BigQuery loading        | For BigQuery |
| `NUMBER_OF_LOCALITIES_PER_PLACE` | Stations per city (default: 3) | No           |

## Output Format

The pipeline generates CSV files with the following schema:

| Column      | Type     | Description                     |
| ----------- | -------- | ------------------------------- |
| `city`      | string   | City name                       |
| `location`  | string   | Monitoring station name         |
| `parameter` | string   | Pollutant (pm25, pm10, o3, no2) |
| `value`     | float    | Measurement value               |
| `unit`      | string   | Unit of measurement (µg/m³)     |
| `timestamp` | datetime | Measurement timestamp (UTC)     |

**Example:**

```csv
city;location;parameter;value;unit;timestamp
Warsaw;Warszawa-Komunikacyjna;pm25;18.5;µg/m³;2025-12-14T12:00:00+00:00
London;London Marylebone Road;no2;42.3;µg/m³;2025-12-14T12:00:00+00:00
```

## Deployment

### Deploy to Google Cloud Functions

The project includes a deployment script that runs tests and deploys to Cloud Functions.

**Prerequisites:**

- Google Cloud SDK installed and authenticated (`gcloud auth login`)
- Proper permissions (Cloud Functions Developer, Storage Admin)

**Deploy:**

```bash
./deploy.sh
```

The script will:

1. Load environment variables from `.env`
2. Run all tests (`pytest tests/ -v`)
3. Ask for confirmation
4. Deploy to Cloud Functions Gen2 with your configuration

**Manual deployment (without script):**

```bash
gcloud functions deploy air-quality-etl \
  --gen2 \
  --runtime=python311 \
  --region=europe-central2 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="OPENAQ_API_KEY=xxx,GCS_BUCKET_NAME=xxx,..."
```

### Invoke the Function

```bash
# Using gcloud
gcloud functions call air-quality-etl --region=europe-central2

# Using curl (requires authentication)
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://YOUR_FUNCTION_URL
```

### Scheduled Execution

Use **Cloud Scheduler** to run the pipeline periodically:

```bash
gcloud scheduler jobs create http air-quality-hourly \
  --location=europe-central2 \
  --schedule="0 * * * *" \
  --uri="https://FUNCTION_URL" \
  --oidc-service-account-email=YOUR_SA@PROJECT.iam.gserviceaccount.com
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_validators.py

# Run with coverage
pytest --cov=. --cov-report=html
```

## Configuration

### Adding New Cities

Edit `config/places.py`:

```python
PLACES = [
    Place(country_iso="PL", city_aliases=["Warsaw", "Warszawa"]),
    Place(country_iso="GB", city_aliases=["London"]),
    Place(country_iso="DE", city_aliases=["Berlin"]),  # Add new city
]
```

### Monitored Pollutants

Defined in `domain/models.py`:

```python
class AirQualityParameter(Enum):
    PM25 = "pm25"
    PM10 = "pm10"
    O3 = "o3"
    NO2 = "no2"
```

## License

MIT License

## Author

Piotr Szewczak
