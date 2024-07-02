#!/bin/bash

# Ensure PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo "PROJECT_ID is not set. Using 'gcloud config get-value project'."
    PROJECT_ID=$(gcloud config get-value project)
fi

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

echo "PROJECT_NUMBER: $PROJECT_NUMBER"

# Read environment variables from .env file
ENV_VARS=$(grep -v '^#' .env | sed 's/^/--set-env-vars /' | tr '\n' ' ')

# Print the command that will be executed (without actual env var values)
echo "Executing command:"
SERVICE_NAME=${1:-discord-bot}
echo "gcloud builds submit --config=cloudbuild.yaml --substitutions=_SERVICE_ACCOUNT=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com,_SERVICE_NAME=$SERVICE_NAME,_ENV_VARS=\"${ENV_VARS}\""
# Submit the build
gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_SERVICE_ACCOUNT=${PROJECT_NUMBER}-compute@developer.gserviceaccount.com,_SERVICE_NAME=$SERVICE_NAME,_ENV_VARS="${ENV_VARS}"

# If the build was successful, describe the service
if [ $? -eq 0 ]; then
    echo "Deployment successful. Fetching service URL..."
    gcloud run services describe $SERVICE_NAME --platform managed --region us-central1 --format 'value(status.url)'
else
    echo "Deployment failed. Please check the build logs."
fi