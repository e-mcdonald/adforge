output "ec2_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.adforge.public_ip
}

output "s3_bucket_name" {
  description = "S3 bucket for campaign images"
  value       = aws_s3_bucket.adforge_images.bucket
}

output "ecr_backend_url" {
  description = "ECR URL for backend image"
  value       = aws_ecr_repository.adforge_backend.repository_url
}

output "ecr_frontend_url" {
  description = "ECR URL for frontend image"
  value       = aws_ecr_repository.adforge_frontend.repository_url
}
