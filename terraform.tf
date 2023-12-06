terraform {
  required_version = "= 1.6.4"

  backend "s3" {
    bucket         = "luciferous-devio-index-2023-bucketterraformstates-148xtc3n4j09n"
    key            = "cloud/cloud.tfstate"
    dynamodb_table = "luciferous-devio-index-2023-prepare-LockTableCloud-19VRBM1KV68Y6"
  }
}

module "common" {
  source = "./terraform_modules/common"

  notion_token = var.notion_token
}

variable "notion_token" {
  type      = string
  nullable  = false
  sensitive = true
}
