locals {
  name = "${var.project_name}-${var.environment}"
}

# ---------------------------------------------------------------------------
# Network: use the account's default VPC to keep things simple and free.
# ---------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Latest Amazon Linux 2023 image, looked up from AWS's public parameter.
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

resource "aws_security_group" "app" {
  name        = "${local.name}-sg"
  description = "HTTP access to the Tips Splitter API. No SSH: access is via SSM."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.allowed_http_cidr]
  }

  egress {
    description = "Outbound (package installs, pulling images from ECR)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------------------------
# Container registry: the CD pipeline (Phase 2) pushes Docker images here.
# ---------------------------------------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the last 5 images to stay inside the free storage"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# ---------------------------------------------------------------------------
# Permissions for the server: pull images, be managed by SSM, send logs.
# ---------------------------------------------------------------------------
resource "aws_iam_role" "app" {
  name = "${local.name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "app" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
  ])

  role       = aws_iam_role.app.name
  policy_arn = each.value
}

resource "aws_iam_instance_profile" "app" {
  name = "${local.name}-instance-profile"
  role = aws_iam_role.app.name
}

# ---------------------------------------------------------------------------
# Logs: the container sends its JSON logs here (Phase 2 monitoring).
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "app" {
  name              = "/${var.project_name}/${var.environment}"
  retention_in_days = var.log_retention_days
}

# ---------------------------------------------------------------------------
# Server: one small EC2 instance with Docker installed.
# ---------------------------------------------------------------------------
resource "aws_instance" "app" {
  ami                         = data.aws_ssm_parameter.al2023_ami.value
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    aws_region = var.aws_region
    ecr_url    = aws_ecr_repository.app.repository_url
    app_port   = var.app_port
    log_group  = aws_cloudwatch_log_group.app.name
  })
  user_data_replace_on_change = true

  # Security hardening: IMDSv2 only and encrypted disk.
  metadata_options {
    http_tokens   = "required"
    http_endpoint = "enabled"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
    encrypted   = true
  }

  tags = {
    Name = local.name
  }
}
