terraform {
  required_version = "= 1.6.4"

  backend "s3" {
    bucket         = "luciferous-devio-index-2023-bucketterraformstates-148xtc3n4j09n"
    key            = "cloud/cloud.tfstate"
    dynamodb_table = "luciferous-devio-index-2023-prepare-LockTable-Y76P2668G3P9"
  }

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

module "common" {
  source = "./terraform_modules/common"

  notion_token               = var.notion_token
  notion_database_id         = var.notion_database_id
  cloudflare_deploy_hook_url = var.cloudflare_deploy_hook_url
  region                     = var.region
  system_name                = var.system_name
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
  default  = "ap-northeast-1"
}

variable "system_name" {
  type     = string
  nullable = false
  default  = "luciferous-devio-index-reinvent-2023"
}

output "sns_error_topic_url" {
  value = module.common.sns_topic_error_url
}