#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Sentinel AI — Backend Deployment to Azure App Service
#
# Deploys the FastAPI Investigation Gateway as a Linux container on
# Azure App Service, backed by Azure Container Registry (ACR).
#
# Prerequisites:
#   - Azure CLI installed and logged in: az login
#   - An Azure subscription with permission to create resources
#
# Usage:
#   chmod +x deploy/azure-deploy-backend.sh
#   ./deploy/azure-deploy-backend.sh
#
# All values can be overridden via environment variables before running.
# ─────────────────────────────────────────────
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-sentinel-ai-rg}"
LOCATION="${LOCATION:-eastus}"
ACR_NAME="${ACR_NAME:-sentinelaiacr$RANDOM}"
APP_SERVICE_PLAN="${APP_SERVICE_PLAN:-sentinel-ai-plan}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-sentinel-ai-backend}"
IMAGE_NAME="sentinel-ai-backend"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SKU="${SKU:-B1}"

echo "── Sentinel AI Backend Deployment ──────────────────────────"
echo "Resource Group:  $RESOURCE_GROUP"
echo "Location:        $LOCATION"
echo "ACR Name:         $ACR_NAME"
echo "App Service Plan:  $APP_SERVICE_PLAN"
echo "Backend App Name:   $BACKEND_APP_NAME"
echo "──────────────────────────────────────────────────────────────"

# 1. Resource group
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# 2. Azure Container Registry
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  --output table

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)

# 3. Build & push the backend image using ACR Tasks (no local Docker required)
echo "Building backend image in ACR..."
az acr build \
  --registry "$ACR_NAME" \
  --image "$IMAGE_NAME:$IMAGE_TAG" \
  --file Dockerfile \
  .

# 4. App Service Plan (Linux)
az appservice plan create \
  --name "$APP_SERVICE_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --is-linux \
  --sku "$SKU" \
  --output table

# 5. Web App for Containers
az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_SERVICE_PLAN" \
  --name "$BACKEND_APP_NAME" \
  --deployment-container-image-name "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
  --output table

# 6. Configure registry credentials for the Web App
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

az webapp config container set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --container-image-name "$ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG" \
  --container-registry-url "https://$ACR_LOGIN_SERVER" \
  --container-registry-user "$ACR_USERNAME" \
  --container-registry-password "$ACR_PASSWORD"

# 7. App settings — environment variables consumed by core/config.py
#    Defaults to mock mode so the app works immediately on deploy.
#    Override these in the Azure Portal (App Service > Configuration)
#    or by re-running this command with real values.
az webapp config appsettings set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    SENTINEL_MOCK_MODE="${SENTINEL_MOCK_MODE:-true}" \
    AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}" \
    AZURE_OPENAI_KEY="${AZURE_OPENAI_KEY:-}" \
    AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-gpt-4o}" \
    OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    FOUNDRY_PROJECT_ENDPOINT="${FOUNDRY_PROJECT_ENDPOINT:-}" \
    FOUNDRY_MODEL_DEPLOYMENT="${FOUNDRY_MODEL_DEPLOYMENT:-gpt-4o}" \
    WEBSITES_PORT="8000" \
  --output table

# 8. Enable continuous deployment-friendly settings (always-on, container start time)
az webapp config set \
  --name "$BACKEND_APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --always-on true \
  --output table

BACKEND_URL="https://$(az webapp show --name "$BACKEND_APP_NAME" --resource-group "$RESOURCE_GROUP" --query defaultHostName -o tsv)"

echo ""
echo "✅ Backend deployed:"
echo "   $BACKEND_URL"
echo "   Health check: $BACKEND_URL/health"
echo "   API docs:     $BACKEND_URL/docs"
echo ""
echo "Use this URL as NEXT_PUBLIC_API_URL when deploying the frontend:"
echo "   export NEXT_PUBLIC_API_URL=\"$BACKEND_URL\""
