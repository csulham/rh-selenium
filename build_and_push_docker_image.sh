#!/bin/bash
# Define variables
project_id="rh-marketing-analytics-ga4"
source_code_bucket="automation-qa"
artifact_registry_repository="qa-selenium-test"
docker_image_name="docker-img-qa-selenium-test"

# Create a directory for the App:
mkdir app
cd app

# Setup current project:
gcloud config set project $project_id

# Make shure the current project is "rh-marketing-analytics-ga4":
echo "Current project: "
gcloud config get-value project 

# Enable needed services:
gcloud services enable artifactregistry.googleapis.com

# Copy the source code from GCS to your Cloud Shell session:
gsutil -m cp -r gs://$source_code_bucket/* .

# Build the Docker Image:
docker build -t us-central1-docker.pkg.dev/$project_id/$artifact_registry_repository/$docker_image_name .

# Upload the Docker Image to Artifact Registry:
docker push us-central1-docker.pkg.dev/$project_id/$artifact_registry_repository/$docker_image_name