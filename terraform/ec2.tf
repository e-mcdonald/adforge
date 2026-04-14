# Amazon Linux 2023 AMI — us-east-1
# Update AMI ID for other regions via: aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-*-x86_64"
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_instance" "adforge" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.adforge.name
  vpc_security_group_ids = [aws_security_group.adforge.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/userdata.sh.tpl", {
    aws_region      = var.aws_region
    ecr_backend_url = aws_ecr_repository.adforge_backend.repository_url
    ecr_frontend_url = aws_ecr_repository.adforge_frontend.repository_url
    s3_bucket       = aws_s3_bucket.adforge_images.bucket
  })

  tags = {
    Name = "${var.app_name}-${var.environment}"
    App  = var.app_name
    Env  = var.environment
  }
}
