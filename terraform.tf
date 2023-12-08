terraform {
  required_version = "= 1.6.4"

  backend "s3" {
    bucket         = "luciferous-devio-index-2023-bucketterraformstates-148xtc3n4j09n"
    key            = "cloud/cloud.tfstate"
    dynamodb_table = "luciferous-devio-index-2023-prepare-LockTable-Y76P2668G3P9"
  }
}

module "common" {
  source = "./terraform_modules/common"

  notion_token               = var.notion_token
  cloudflare_deploy_hook_url = var.cloudflare_deploy_hook_url
}

variable "notion_token" {
  type      = string
  nullable  = false
  sensitive = true
}

variable "cloudflare_deploy_hook_url" {
  type      = string
  nullable  = false
  sensitive = true
}

output "sns_error_topic_url" {
  value = module.common.sns_topic_error_url
}