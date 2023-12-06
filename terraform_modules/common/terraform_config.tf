terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.26"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"

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

variable "system_name" {
  type     = string
  nullable = false
  default  = "luciferous-devio-index-reinvent-2023"
}
