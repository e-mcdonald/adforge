resource "aws_s3_bucket" "adforge_images" {
  bucket = "${var.app_name}-images-${var.environment}"

  tags = {
    App  = var.app_name
    Env  = var.environment
  }
}

resource "aws_s3_bucket_versioning" "adforge_images" {
  bucket = aws_s3_bucket.adforge_images.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "adforge_images" {
  bucket = aws_s3_bucket.adforge_images.id

  rule {
    id     = "expire-old-images"
    status = "Enabled"

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adforge_images" {
  bucket = aws_s3_bucket.adforge_images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
