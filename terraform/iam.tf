resource "aws_iam_role" "adforge_ec2" {
  name = "${var.app_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = {
    App  = var.app_name
    Env  = var.environment
  }
}

# S3 access scoped to adforge bucket only
resource "aws_iam_policy" "s3_adforge" {
  name = "${var.app_name}-s3-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
      ]
      Resource = [
        aws_s3_bucket.adforge_images.arn,
        "${aws_s3_bucket.adforge_images.arn}/*",
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.adforge_ec2.name
  policy_arn = aws_iam_policy.s3_adforge.arn
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.adforge_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.adforge_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# SSM read for secrets
resource "aws_iam_policy" "ssm_read" {
  name = "${var.app_name}-ssm-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
      ]
      Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/adforge/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.adforge_ec2.name
  policy_arn = aws_iam_policy.ssm_read.arn
}

resource "aws_iam_instance_profile" "adforge" {
  name = "${var.app_name}-instance-profile"
  role = aws_iam_role.adforge_ec2.name
}
