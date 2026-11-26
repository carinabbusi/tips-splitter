variable "aws_region" {
  description = "AWS region. eu-north-1 is Stockholm."
  type        = string
  default     = "eu-north-1"
}

variable "project_name" {
  description = "Prefix used to name every resource."
  type        = string
  default     = "tips-splitter"
}

variable "environment" {
  description = "Environment name (staging, production...)."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "environment must be staging or production."
  }
}

variable "instance_type" {
  description = "EC2 size. t3.micro is free tier eligible."
  type        = string
  default     = "t3.micro"
}

variable "app_port" {
  description = "Port the container listens on inside the server."
  type        = number
  default     = 8000
}

variable "allowed_http_cidr" {
  description = "Who can reach the API over HTTP. Restrict to your own IP if you prefer."
  type        = string
  default     = "0.0.0.0/0"
}

variable "log_retention_days" {
  description = "How long CloudWatch keeps application logs."
  type        = number
  default     = 7
}

variable "github_repo" {
  description = "GitHub repository allowed to deploy (owner/name)."
  type        = string
  default     = "carinabbusi/tips-splitter"
}

variable "alert_email" {
  description = "Email that receives CloudWatch alarms. Empty = no email."
  type        = string
  default     = ""
}
