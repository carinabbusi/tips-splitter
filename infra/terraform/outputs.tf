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

output "github_actions_role_arn" {
  description = "Role assumed by GitHub Actions (repo variable AWS_ROLE_ARN)."
  value       = aws_iam_role.github_actions.arn
}

output "aws_region" {
  description = "Region used by the pipeline (repo variable AWS_REGION)."
  value       = var.aws_region
}
