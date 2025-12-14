#!/bin/bash
#
# Deploy script for Air Quality ETL Pipeline
# Runs tests locally and deploys to Google Cloud Functions if successful
#
# Usage: ./deploy.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables from .env file
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Configuration
FUNCTION_NAME="air-quality-etl"
REGION="europe-central2"
RUNTIME="python311"
ENTRY_POINT="main"
MEMORY="256MB"
TIMEOUT="300s"

echo "========================================"
echo "  Air Quality ETL Pipeline - Deploy"
echo "========================================"
echo ""

# Step 1: Run tests
echo -e "${YELLOW}[1/3] Running tests...${NC}"
echo ""

if pytest tests/ -v; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo ""
    echo -e "${RED}✗ Tests failed. Aborting deployment.${NC}"
    exit 1
fi

echo ""

# Step 2: Confirm deployment
echo -e "${YELLOW}[2/3] Preparing deployment...${NC}"
echo ""
echo "Function name:  ${FUNCTION_NAME}"
echo "Region:         ${REGION}"
echo "Runtime:        ${RUNTIME}"
echo "Project:        ${GOOGLE_CLOUD_PROJECT}"
echo "GCS Bucket:     ${GCS_BUCKET_NAME}"
echo "BigQuery:       ${BIGQUERY_ENABLED}"
echo ""

read -p "Deploy to Google Cloud Functions? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    exit 0
fi

# Step 3: Deploy to Cloud Functions
echo ""
echo -e "${YELLOW}[3/3] Deploying to Cloud Functions...${NC}"
echo ""

gcloud functions deploy ${FUNCTION_NAME} \
    --gen2 \
    --runtime=${RUNTIME} \
    --region=${REGION} \
    --source=. \
    --entry-point=${ENTRY_POINT} \
    --trigger-http \
    --allow-unauthenticated \
    --memory=${MEMORY} \
    --timeout=${TIMEOUT} \
    --set-env-vars="\
BASE_OPENAQ_URL=${BASE_OPENAQ_URL},\
OPENAQ_API_KEY=${OPENAQ_API_KEY},\
NUMBER_OF_LOCALITIES_PER_PLACE=${NUMBER_OF_LOCALITIES_PER_PLACE},\
GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},\
GCS_BUCKET_NAME=${GCS_BUCKET_NAME},\
BIGQUERY_PROJECT_ID=${BIGQUERY_PROJECT_ID},\
BIGQUERY_ENABLED=${BIGQUERY_ENABLED}"

echo ""
echo -e "${GREEN}========================================"
echo "  ✓ Deployment successful!"
echo "========================================${NC}"
echo ""

# Get and display function URL
FUNCTION_URL=$(gcloud functions describe ${FUNCTION_NAME} \
    --gen2 \
    --region=${REGION} \
    --format="value(serviceConfig.uri)")

echo "Function URL: ${FUNCTION_URL}"
echo ""
echo "To invoke the function:"
echo "  gcloud functions call ${FUNCTION_NAME} --region=${REGION}"
echo ""
echo "Or with curl:"
echo "  curl -H \"Authorization: Bearer \$(gcloud auth print-identity-token)\" ${FUNCTION_URL}"
