resource "aws_ssm_parameter" "notion_token" {
  name  = "/LuciferousDevioIndexReinvent2023/NotionToken"
  type  = "SecureString"
  value = var.notion_token
}