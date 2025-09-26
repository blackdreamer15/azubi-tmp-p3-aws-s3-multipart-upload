variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for file uploads"
  type        = string
  default     = "s3-multipart-upload-dev"
}

variable "max_file_size" {
  description = "Maximum file size in bytes (default: 100MB)"
  type        = number
  default     = 104857600
}

variable "allowed_file_types" {
  description = "List of allowed file extensions"
  type        = list(string)
  default     = [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".zip", ".txt", ".doc", ".docx"]
}
