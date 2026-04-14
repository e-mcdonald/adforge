#!/bin/bash
set -e

# Install Docker
dnf update -y
dnf install -y docker
systemctl start docker
systemctl enable docker
usermod -aG docker ec2-user

# Install Docker Compose v2
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install AWS CLI v2 (already present on AL2023 but ensure latest)
dnf install -y aws-cli

# Fetch secrets from SSM
OPENAI_KEY=$(aws ssm get-parameter --name /adforge/OPENAI_API_KEY --with-decryption --region ${aws_region} --query Parameter.Value --output text)
ANTHROPIC_KEY=$(aws ssm get-parameter --name /adforge/ANTHROPIC_API_KEY --with-decryption --region ${aws_region} --query Parameter.Value --output text)

# Write .env
mkdir -p /opt/adforge
cat > /opt/adforge/.env <<EOF
OPENAI_API_KEY=$OPENAI_KEY
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
OLLAMA_BASE_URL=http://localhost:11434
ENV=production
AWS_REGION=${aws_region}
S3_BUCKET=${s3_bucket}
EOF

# Log into ECR
aws ecr get-login-password --region ${aws_region} | \
  docker login --username AWS --password-stdin ${ecr_backend_url}

# Pull images
docker pull ${ecr_backend_url}:latest
docker pull ${ecr_frontend_url}:latest

# Write docker-compose for production
cat > /opt/adforge/docker-compose.yml <<COMPOSE
version: "3.9"
services:
  backend:
    image: ${ecr_backend_url}:latest
    ports:
      - "8000:8000"
    env_file: /opt/adforge/.env
    volumes:
      - campaign_images:/app/static/campaigns
    restart: unless-stopped
  frontend:
    image: ${ecr_frontend_url}:latest
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
volumes:
  campaign_images:
COMPOSE

# Start
cd /opt/adforge
docker-compose up -d
