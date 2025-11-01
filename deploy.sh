#!/bin/bash

# SmartShopper AI - Cloud Run GPU Deployment Script
# This script deploys the application to Google Cloud Run with L4 GPU support

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SmartShopper AI - Cloud Run GPU Deployment       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: PROJECT_ID environment variable is not set${NC}"
    echo "Please set it with: export PROJECT_ID=your-project-id"
    exit 1
fi

# Configuration
REGION="europe-west1"
SERVICE_NAME="smartshopper-ai-gpu"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo -e "${GREEN}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service Name: $SERVICE_NAME"
echo "  Image: $IMAGE_NAME:latest"
echo ""

# Enable required APIs
echo -e "${BLUE}[1/5] Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    --project=$PROJECT_ID

# Build the Docker image
echo -e "${BLUE}[2/5] Building Docker image with GPU support...${NC}"
gcloud builds submit --tag $IMAGE_NAME:latest \
    --timeout=3600s \
    --machine-type=e2-highcpu-8 \
    --project=$PROJECT_ID \
    -f Dockerfile.gpu \
    .

# Deploy to Cloud Run
echo -e "${BLUE}[3/5] Deploying to Cloud Run with L4 GPU...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 8Gi \
    --cpu 4 \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1" \
    --project=$PROJECT_ID

# Get the service URL
echo -e "${BLUE}[4/5] Retrieving service URL...${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --format 'value(status.url)' \
    --project=$PROJECT_ID)

# Test the deployment
echo -e "${BLUE}[5/5] Testing deployment...${NC}"
if curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Service is healthy!${NC}"
else
    echo -e "${RED}⨯ Health check failed${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Deployment Successful! 🚀                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Service URL:${NC} $SERVICE_URL"
echo ""
echo "API Endpoints:"
echo "  • Health Check: $SERVICE_URL/health"
echo "  • Text Search:  $SERVICE_URL/api/search (POST)"
echo "  • Visual Search: $SERVICE_URL/api/visual-search (POST)"
echo "  • Chat: $SERVICE_URL/api/chat (POST)"
echo ""
echo "Test visual search with:"
echo "  curl -X POST -F 'image=@/path/to/product-image.jpg' $SERVICE_URL/api/visual-search"
echo ""
