output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.file_upload_bucket.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.file_upload_bucket.arn
}

output "kms_key_id" {
  description = "KMS key ID for encryption"
  value       = aws_kms_key.s3_encryption_key.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.s3_encryption_key.arn
}

output "uploader_role_arn" {
  description = "ARN of the uploader IAM role"
  value       = aws_iam_role.uploader_role.arn
}

output "viewer_role_arn" {
  description = "ARN of the viewer IAM role"
  value       = aws_iam_role.viewer_role.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.s3_upload_logs.name
}

output "cloudwatch_alarm_arn" {
  description = "CloudWatch alarm ARN for unauthorized access"
  value       = aws_cloudwatch_metric_alarm.unauthorized_access.arn
}

# Cognito outputs
output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "cognito_identity_pool_id" {
  description = "Cognito Identity Pool ID"
  value       = aws_cognito_identity_pool.main.id
}

output "cognito_domain" {
  description = "Cognito User Pool Domain"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "cognito_authenticated_role_arn" {
  description = "ARN of the Cognito authenticated role"
  value       = aws_iam_role.cognito_authenticated_role.arn
}
