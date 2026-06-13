#!/usr/bin/env bash
# ─────────────────────────────────────────────
# Sentinel AI — Frontend Deployment to Azure Static Web Apps
#
# Azure Static Web Apps (free tier available) is the fastest path for a
# Next.js frontend during a hackathon — no container registry needed.
#
# Prerequisites:
#   - Azure CLI installed and logged in: az login
#   - Static Web Apps CLI: npm install -g @azure/static-web-apps-cli
#   - The backend already deployed (see azure-deploy-backend.sh) so you
#     have a NEXT_PUBLIC_API_URL to point at.
#
# Usage:
#   export NEXT_PUBLIC_API_URL="https://sentinel-ai-backend.azurewebsites.net"
#   chmod +x deploy/azure-deploy-frontend.sh
#   ./deploy/azure-deploy-frontend.sh
# ─────────────────────────────────────────────
set -euo pipefail

RESOURCE_GROUP="${RESOURCE_GROUP:-sentinel-ai-rg}"
LOCATION="${LOCATION:-eastus2}"   # Static Web Apps has a limited region list
SWA_NAME="${SWA_NAME:-sentinel-ai-frontend}"
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

echo "── Sentinel AI Frontend Deployment (Static Web Apps) ───────"
echo "Resource Group:   $RESOURCE_GROUP"
echo "Location:         $LOCATION"
echo "Static Web App:    $SWA_NAME"
echo "Backend API URL:    $NEXT_PUBLIC_API_URL"
echo "──────────────────────────────────────────────────────────────"

# 1. Resource group (idempotent if already created by backend script)
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --output table

# 2. Build the Next.js app with the backend URL baked in
cd "$(dirname "$0")/../frontend"
echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL" > .env.production.local
npm ci
npm run build

# 3. Create the Static Web App (Free tier)
az staticwebapp create \
  --name "$SWA_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Free \
  --output table

# 4. Get a deployment token and deploy via SWA CLI
DEPLOY_TOKEN=$(az staticwebapp secrets list \
  --name "$SWA_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.apiKey" -o tsv)

npx --yes @azure/static-web-apps-cli deploy \
  --app-location . \
  --output-location .next \
  --deployment-token "$DEPLOY_TOKEN" \
  --env production

FRONTEND_URL="https://$(az staticwebapp show --name "$SWA_NAME" --resource-group "$RESOURCE_GROUP" --query defaultHostname -o tsv)"

echo ""
echo "✅ Frontend deployed:"
echo "   $FRONTEND_URL"
echo ""
echo "──────────────────────────────────────────────────────────────"
echo "ALTERNATIVE: Deploy frontend as a container to App Service instead"
echo "(use this if Static Web Apps' Next.js SSR support is unavailable"
echo "in your region/tier):"
echo ""
echo "  az acr build --registry <ACR_NAME> --image sentinel-ai-frontend:latest \\"
echo "    --file frontend/Dockerfile \\"
echo "    --build-arg NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \\"
echo "    frontend"
echo ""
echo "  az webapp create --resource-group $RESOURCE_GROUP \\"
echo "    --plan sentinel-ai-plan --name sentinel-ai-frontend \\"
echo "    --deployment-container-image-name <ACR_LOGIN_SERVER>/sentinel-ai-frontend:latest"
echo ""
echo "  az webapp config appsettings set --name sentinel-ai-frontend \\"
echo "    --resource-group $RESOURCE_GROUP --settings WEBSITES_PORT=3000"
echo "──────────────────────────────────────────────────────────────"
