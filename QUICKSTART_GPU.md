# 🚀 Quick Start: GPU-Powered Visual Search

This guide will help you deploy SmartShopper AI with GPU-powered visual search to Google Cloud Run.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** (for local testing, optional)

## Step 1: Set Up Google Cloud

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    --project=$PROJECT_ID
```

## Step 2: Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd smartshopper-ai

# Copy environment template
cp .env.template .env

# Edit .env with your configuration
nano .env
```

Update `.env`:
```env
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
FLASK_ENV=production
```

## Step 3: Deploy to Cloud Run

### Option A: Automated Deployment (Recommended)

```bash
chmod +x deploy.sh
./deploy.sh
```

### Option B: Manual Deployment

```bash
# Build the Docker image
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/smartshopper-ai-gpu:latest \
    --timeout=3600s \
    --machine-type=e2-highcpu-8 \
    -f Dockerfile.gpu \
    .

# Deploy to Cloud Run with GPU
gcloud run deploy smartshopper-ai-gpu \
    --image gcr.io/$PROJECT_ID/smartshopper-ai-gpu:latest \
    --region europe-west1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 8Gi \
    --cpu 4 \
    --gpu 1 \
    --gpu-type nvidia-l4 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,VERTEX_AI_LOCATION=us-central1" \
    --project=$PROJECT_ID
```

## Step 4: Get Service URL

```bash
gcloud run services describe smartshopper-ai-gpu \
    --region europe-west1 \
    --format 'value(status.url)'
```

## Step 5: Test the Deployment

### Test Health Endpoint
```bash
curl https://your-service-url.run.app/health
```

### Test Visual Search
```bash
# Download a sample product image
curl -o test-product.jpg https://example.com/product.jpg

# Test visual search
curl -X POST \
    -F "image=@test-product.jpg" \
    https://your-service-url.run.app/api/visual-search
```

### Test from Browser
Open your service URL in a browser and:
1. Click on "Visual Search" tab
2. Upload a product image
3. See real-time results!

## 📊 Monitoring

### View Logs
```bash
gcloud run services logs read smartshopper-ai-gpu \
    --region europe-west1 \
    --limit 50
```

### Monitor Metrics
```bash
# Go to Cloud Console
https://console.cloud.google.com/run/detail/europe-west1/smartshopper-ai-gpu/metrics
```

## 🔧 Troubleshooting

### Build Timeout
If the build times out, increase the timeout:
```bash
--timeout=7200s  # 2 hours
```

### GPU Not Available
Ensure you're using a supported region:
- `europe-west1` (Belgium)
- `europe-west4` (Netherlands)
- `us-central1` (Iowa)

### Memory Issues
If you see OOM errors, increase memory:
```bash
--memory 16Gi
```

### CLIP Model Download Issues
The model is downloaded during build. If it fails:
1. Check your network connectivity
2. Try a different base image
3. Pre-download the model to Cloud Storage

## 💰 Cost Optimization

### Reduce Costs
```bash
# Set min instances to 0 (scale to zero)
--min-instances 0

# Reduce memory if not needed
--memory 4Gi

# Set max instances to control costs
--max-instances 5
```

### Estimated Costs (per month)
- **GPU time**: ~$0.50/hour (L4)
- **CPU time**: ~$0.10/hour (4 vCPU)
- **Memory**: ~$0.01/GB-hour
- **With scale-to-zero**: Pay only when serving requests

Example: 1000 requests/day, avg 2s each = ~$15/month

## 🎯 Next Steps

1. **Add Product Data**: Populate Elasticsearch with your products
2. **Generate Embeddings**: Pre-compute embeddings for existing products
3. **Customize UI**: Update frontend branding and styling
4. **Set Up Monitoring**: Configure alerts and dashboards
5. **Enable Authentication**: Add user authentication if needed

## 📚 Additional Resources

- [Cloud Run GPU Documentation](https://cloud.google.com/run/docs/configuring/services/gpu)
- [CLIP Model Documentation](https://github.com/openai/CLIP)
- [Gemini Vision API](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)

## 🆘 Need Help?

- Check `HACKATHON.md` for detailed architecture
- Review logs: `gcloud run services logs read`
- Open an issue on GitHub

---

**Happy Deploying! 🚀**
