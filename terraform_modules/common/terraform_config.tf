terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.26"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      SystemName = var.system_name
    }
  }
}

variable "notion_token" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "region" {
  type     = string
  nullable = false
  default  = "ap-northeast-1"
}

variable "system_name" {
  type     = string
  nullable = false
  default  = "luciferous-devio-index-reinvent-2023"
}

output "sns_topic_error_url" {
  value = "https://${var.region}.console.aws.amazon.com/sns/v3/home?region=${var.region}#/topic/${aws_sns_topic.error_topic.arn}"
}