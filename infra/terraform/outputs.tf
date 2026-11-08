output "ecr_repository_url" {
  description = "Where the CD pipeline pushes Docker images."
  value       = aws_ecr_repository.app.repository_url
}

output "instance_id" {
  description = "EC2 instance used by the deploy step (via SSM)."
  value       = aws_instance.app.id
}

output "app_url" {
  description = "Public URL of the API once deployed."
  value       = "http://${aws_instance.app.public_dns}"
}

output "log_group" {
  description = "CloudWatch log group for the application."
  value       = aws_cloudwatch_log_group.app.name
}
