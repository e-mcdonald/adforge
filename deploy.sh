#!/bin/bash
set -e

: "${ECR_REGISTRY:?Need to set ECR_REGISTRY}"
: "${AWS_REGION:=us-east-1}"

echo "Building images..."
docker build -t adforge-backend ./backend
docker build -t adforge-frontend ./frontend

echo "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "Tagging and pushing..."
docker tag adforge-backend:latest "$ECR_REGISTRY/adforge-backend:latest"
docker tag adforge-frontend:latest "$ECR_REGISTRY/adforge-frontend:latest"
docker push "$ECR_REGISTRY/adforge-backend:latest"
docker push "$ECR_REGISTRY/adforge-frontend:latest"

echo "Applying Terraform..."
cd terraform
terraform init
terraform apply -auto-approve

echo "Deploy complete. Public IP: $(terraform output -raw ec2_public_ip)"
