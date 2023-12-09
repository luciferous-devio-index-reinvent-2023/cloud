terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.26"
    }
  }
}

variable "notion_token" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "notion_database_id" {
  type     = string
  nullable = false
}

variable "cloudflare_deploy_hook_url" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "region" {
  type     = string
  nullable = false
}

variable "system_name" {
  type     = string
  nullable = false
}

output "sns_topic_error_url" {
  value = "https://${var.region}.console.aws.amazon.com/sns/v3/home?region=${var.region}#/topic/${aws_sns_topic.error_topic.arn}"
}