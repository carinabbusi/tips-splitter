terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Phase 1: state is kept locally (terraform.tfstate, ignored by git).
  # Phase 2: move state to S3 so the CD pipeline can share it, e.g.:
  # backend "s3" {
  #   bucket       = "tips-splitter-tfstate-<your-account-id>"
  #   key          = "staging/terraform.tfstate"
  #   region       = "eu-west-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
