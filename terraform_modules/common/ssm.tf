resource "aws_ssm_parameter" "notion_token" {
  name  = "/LuciferousDevioIndexReinvent2023/NotionToken"
  type  = "SecureString"
  value = var.notion_token
}

resource "aws_ssm_parameter" "cloudflare_deploy_hook_url" {
  name  = "/LuciferousDevioIndexReinvent2023/CloudflareDeployHookUrl"
  type  = "SecureString"
  value = var.cloudflare_deploy_hook_url
}