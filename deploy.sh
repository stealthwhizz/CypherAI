#!/bin/bash
# Quick deploy script for CypherAI to Google Cloud Run
# No fancy error handling. If something breaks, you'll see it.

set -e  # Exit on error

echo "🚀 Deploying CypherAI to Google Cloud Run..."
echo ""

# Check if we have what we need
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Missing GOOGLE_API_KEY environment variable"
    echo "   Set it with: export GOOGLE_API_KEY='your_key'"
    exit 1
fi

# Configuration (change these if you want)
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-cypherai-demo}"
SERVICE_NAME="cypherai-scanner"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo ""

# Make sure gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found"
    echo "   Install it: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📦 Setting project..."
gcloud config set project ${PROJECT_ID} --quiet

# Enable APIs (might already be enabled, that's fine)
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet

# Build the container
echo "🏗️  Building container image..."
echo "   (This takes 2-3 minutes)"
gcloud builds submit --tag ${IMAGE_NAME} --quiet

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
echo "   (This takes another 2-3 minutes)"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --timeout 60s \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
    --set-env-vars "GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET:-}" \
    --set-env-vars "GITHUB_TOKEN=${GITHUB_TOKEN:-}" \
    --quiet

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Your service is live at:"
echo "  $SERVICE_URL"
echo ""
echo "Test it:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "View logs:"
echo "  gcloud run logs tail $SERVICE_NAME --region $REGION"
echo ""
echo "Connect to GitHub:"
echo "  Webhook URL: $SERVICE_URL/webhook"
echo "  Secret: Your GITHUB_WEBHOOK_SECRET value"
echo ""
